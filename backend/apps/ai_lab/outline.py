"""Metadata first. Paragraph text is queried only after the model selects headings."""
from apps.billing.enforcement import require_feature
from . import reference_index
from .models import ReferenceArticle, ReferenceParagraph
from .provider import ProviderError
from .retrieval import Passage


class OutlineReader:
    def __init__(self, request):
        self.request = request
        self.stamp = reference_index.source_stamp()
        self.generation = reference_index.active_generation(self.stamp)
        if not self.generation:
            raise ProviderError("REFERENCE_INDEX_NOT_READY")
        self.articles = {}
        self.sections = {}

    def candidates(self, candidates):
        """Resolve formulation directories using stored link metadata, never bodies."""
        records = {a.source_id: a for a in ReferenceArticle.objects.filter(
            generation_id=self.generation, source_id__in=[c['id'] for c in candidates])}
        expanded = []
        for candidate in candidates:
            record = records.get(candidate['id'])
            if record is not None and record.is_directory:
                expanded.extend(record.related_topics)
            else:
                expanded.append(candidate)
        ids = [c['id'] for c in expanded]
        valid = {a.source_id: a for a in ReferenceArticle.objects.filter(
            generation_id=self.generation, source_id__in=ids).only('source_id', 'title', 'is_directory')}
        result, seen = [], set()
        for candidate in expanded:
            record = valid.get(candidate['id'])
            if record and not record.is_directory and record.source_id not in seen:
                result.append({'id': record.source_id, 'title': record.title})
                seen.add(record.source_id)
        return result[:60]

    def headings(self, articles):
        result = []
        for candidate in articles:
            identifier = candidate['id']
            require_feature(self.request, 'uptodate', item=identifier, consume=False)
            article = ReferenceArticle.objects.get(generation_id=self.generation, source_id=identifier)
            self.articles[identifier] = article
            for section in article.sections.filter(retrieval_order__isnull=False).order_by('ordinal'):
                identifier = 'S' + str(len(self.sections) + 1)
                self.sections[identifier] = section
                result.append({'id': identifier, 'article_id': article.source_id,
                    'title': section.heading, 'path': section.heading_path})
        return result

    def passages(self, identifiers):
        # Only IDs from headings() can reach this method.
        selected = [self.sections[i] for i in identifiers]
        article_ids = {section.article_id for section in selected}
        for article in self.articles.values():
            if article.pk not in article_ids:
                continue
            require_feature(self.request, 'uptodate', item=article.source_id, consume=True)
            if self.stamp.backend == 'mysql':
                with reference_index.mysql_source_connection().cursor() as cursor:
                    cursor.execute('SELECT SHA2(gzip, 256) AS blob_hash FROM content WHERE id = %s', (article.source_id,))
                    row = cursor.fetchone()
                if not row or row['blob_hash'] != article.blob_hash:
                    raise ProviderError('REFERENCE_INDEX_STALE')
        rows = ReferenceParagraph.objects.filter(section_id__in=[s.pk for s in selected],
            retrieval_number__isnull=False).select_related('section', 'article').order_by('article_id', 'ordinal')
        groups = {identifier: [] for identifier in identifiers}
        mapping = {self.sections[i].pk: i for i in identifiers}
        for row in rows:
            article, section = row.article, row.section
            number = 'P' + str(row.pk)  # Global within the prepared generation, including across articles.
            groups[mapping[section.pk]].append(Passage(number, article.source_id, article.title, section.heading, row.text,
                {'screen': 'uptodateArticle', 'params': {'id': article.source_id, 'title': article.title,
                 'sectionId': section.source_id, 'searchAnchor': row.source_anchor, 'searchContentHash': article.content_hash}}, article.content_hash,
                 heading_path=tuple(section.heading_path)))
        self.validate()
        return [p for identifier in identifiers for p in groups[identifier]]

    def validate(self):
        if reference_index.source_stamp() != self.stamp or reference_index.active_generation(self.stamp) != self.generation:
            raise ProviderError('REFERENCE_INDEX_STALE')
