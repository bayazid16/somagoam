from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank
from rest_framework import filters

class PostgresFullTextSearchFilter(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get('search') #search term is coming from query parameter
        
        if not search_term:
            return queryset

        
        vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
        query = SearchQuery(search_term)

        
        return queryset.annotate(
            rank=SearchRank(vector, query)
        ).filter(rank__gte=0.1).order_by('-rank')