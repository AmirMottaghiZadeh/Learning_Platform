import json
from concurrent.futures import ThreadPoolExecutor
from django.core.management.base import BaseCommand, CommandError
from apps.ai_lab import reference_index
from apps.ai_lab.models import ReferenceArticle
from apps.ai_retrieval import source_links
from apps.ai_retrieval.models import SourceLinkMap


class Command(BaseCommand):
    help = "Prepare/resume source-owned link maps; no embeddings, LLM requests or vector rebuild."

    def add_arguments(self, parser):
        parser.add_argument("--workers",type=int,default=2)
        parser.add_argument("--batch-size",type=int,default=50)
        parser.add_argument("--limit",type=int)
        parser.add_argument("--status",action="store_true")

    def handle(self,*args,**options):
        workers,batch=options["workers"],options["batch_size"]
        if not 1<=workers<=8 or not 1<=batch<=500 or (options["limit"] is not None and options["limit"]<1):
            raise CommandError("INVALID_LINK_BUILD_OPTIONS")
        stamp=reference_index.source_stamp()
        generation=reference_index.active_generation(stamp)
        if generation is None:raise CommandError("REFERENCE_INDEX_NOT_READY")
        version=f"{source_links.VERSION}:{source_links.EXTRACTION_VERSION}"
        rows=ReferenceArticle.objects.filter(generation_id=generation).only("source_id","content_hash","generation_id").order_by("source_id")
        if options["limit"]:rows=rows[:options["limit"]]
        known=set(SourceLinkMap.objects.filter(source_generation=generation,parser_version=version)
                  .values_list("source_id","content_hash"))
        articles=list(rows)
        pending=[a for a in articles if (a.source_id,a.content_hash) not in known]
        self.stdout.write(json.dumps({"total":len(articles),"ready":len(articles)-len(pending),"pending":len(pending),"provider_requests":0}),ending="\n")
        self.stdout.flush()
        if options["status"]:return
        done=len(articles)-len(pending)
        with ThreadPoolExecutor(max_workers=workers,thread_name_prefix="source-link-build") as pool:
            for at in range(0,len(pending),batch):
                selected=pending[at:at+batch]
                try:
                    # The snapshot reader caches SQLite connections. Keep its
                    # I/O on the command thread and parallelize pure parsing.
                    raw=[source_links.services.get_topic(a.source_id,include_memberships=False) for a in selected]
                    maps=list(pool.map(lambda pair:source_links.parse(*pair),zip(selected,raw)))
                except Exception as exc:raise CommandError(f"REFERENCE_LINK_BUILD_FAILED code={getattr(exc,'code','PARSING_FAILED')}") from None
                if reference_index.source_stamp()!=stamp:raise CommandError("REFERENCE_INDEX_STALE")
                SourceLinkMap.objects.bulk_create([SourceLinkMap(source_generation=generation,source_id=a.source_id,
                    content_hash=a.content_hash,parser_version=version,links=links) for a,links in zip(selected,maps)],
                    ignore_conflicts=True,batch_size=batch)
                done+=len(selected)
                self.stdout.write(json.dumps({"built":done,"total":len(articles),"provider_requests":0}))
                self.stdout.flush()
