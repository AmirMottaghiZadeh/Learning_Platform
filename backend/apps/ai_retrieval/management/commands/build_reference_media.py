"""Resume media metadata extraction on the active generation, with zero model calls."""
from hashlib import sha256
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import get_context
import time
from django.conf import settings
from django.core.management.base import BaseCommand,CommandError
from django.db import transaction
from apps.ai_lab import reference_index
from apps.uptodate import services
from apps.ai_retrieval.media_catalog import catalog_media,initialize_worker
from apps.ai_retrieval.chunking import source_metadata
from apps.ai_retrieval.models import RetrievalHead,IndexedArticle,ReferenceMedia


class Command(BaseCommand):
    help="Build/resume original table and figure-caption search metadata; no embedding API."

    def add_arguments(self,parser):
        parser.add_argument("--limit",type=int,default=0)
        parser.add_argument("--status",action="store_true")
        parser.add_argument("--rebuild",action="store_true")
        parser.add_argument("--workers",type=int,default=2)

    def handle(self,*args,**options):
        stamp=reference_index.source_stamp()
        head=RetrievalHead.objects.select_related("active").filter(pk=stamp.identity).first()
        generation=head.active if head else None
        if not generation or generation.status!="ready":raise CommandError("HYBRID_INDEX_NOT_READY")
        alias=settings.AI_RETRIEVAL_DATABASE_ALIAS
        if options["rebuild"]:
            with transaction.atomic(using=alias):
                ReferenceMedia.objects.filter(generation=generation).delete()
                IndexedArticle.objects.filter(generation=generation).update(media_built=False)
        indexed=IndexedArticle.objects.filter(generation=generation)
        total=indexed.count();done=indexed.filter(media_built=True).count()
        if options["status"]:
            self.stdout.write(f"Media articles={done}/{total}; items={ReferenceMedia.objects.filter(generation=generation).count()}; model_requests=0.");return
        remaining=list(indexed.filter(media_built=False).order_by("source_id").values_list("pk","source_id","content_hash"))
        if options["limit"]:remaining=remaining[:options["limit"]]
        started=time.monotonic();items=0
        workers=max(1,min(4,options["workers"]))
        with ProcessPoolExecutor(max_workers=workers,mp_context=get_context("spawn"),initializer=initialize_worker) as pool:
            for offset in range(0,len(remaining),32):
                batch=remaining[offset:offset+32];articles=[]
                for pk,identifier,content_hash in batch:
                    article=services.get_topic(identifier,include_memberships=False)
                    if article is None or sha256(article["body_html"].encode()).hexdigest()!=content_hash:raise CommandError("REFERENCE_INDEX_STALE")
                    articles.append(article)
                for (pk,identifier,content_hash),article,found in zip(batch,articles,pool.map(catalog_media,articles)):
                    records=[]
                    for item in found:
                        complete=len(item["text"])<=12000
                        text=item["text"] if complete else item["caption"] or item["title"]
                        description="\n".join(dict.fromkeys(filter(None,[item["title"],item["caption"],text])))
                        audience,_=source_metadata(article["title"],[])
                        records.append(ReferenceMedia(generation=generation,source_id=identifier,content_hash=content_hash,
                            media_key=item["key"],kind=item["kind"],article_title=article["title"],title=item["title"],
                            caption=item["caption"],search_text=f"{article['title']} {item['kind']} {item['title']} {item['text'][:20000]}",
                            evidence_text=description,audience=audience,descriptor={"graphic_hash":item.get("graphic_hash",""),"content_complete":complete}))
                    with transaction.atomic(using=alias):
                        ReferenceMedia.objects.filter(generation=generation,source_id=identifier).delete()
                        ReferenceMedia.objects.bulk_create(records,batch_size=100)
                        IndexedArticle.objects.filter(pk=pk).update(media_built=True)
                    done+=1;items+=len(records)
                    if done%100==0:self.stdout.write(f"Media articles={done}/{total}; new_items={items}; elapsed_s={time.monotonic()-started:.1f}; model_requests=0.")
        if reference_index.source_stamp()!=stamp:raise CommandError("REFERENCE_INDEX_STALE")
        self.stdout.write(f"Media articles={done}/{total}; items={ReferenceMedia.objects.filter(generation=generation).count()}; model_requests=0.")
