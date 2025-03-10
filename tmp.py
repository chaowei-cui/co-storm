import dspy
from typing import Callable, Union, List
from semanticscholar import SemanticScholar
import logging
import json
from typing import List, Union
import scipdf
from knowledge_storm.utils import WebPageHelper


class ScholarSearch(dspy.Retrieve):
    def __init__(
        self,
        bing_search_api_key=None,
        k=3,
        is_valid_source: Callable = None,
        min_char_count: int = 150,
        snippet_chunk_size: int = 1000,
        webpage_helper_max_threads=10,
        mkt="en-US",
        language="en",

        **kwargs,
    ):
        """
        Params:
            min_char_count: Minimum character count for the article to be considered valid.
            snippet_chunk_size: Maximum character count for each snippet.
            webpage_helper_max_threads: Maximum number of threads to use for webpage helper.
            mkt, language, **kwargs: Bing search API parameters.
            - Reference: https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/query-parameters
        """
        super().__init__(k=k)
        # if not bing_search_api_key and not os.environ.get("BING_SEARCH_API_KEY"):
        #     raise RuntimeError(
        #         "You must supply bing_search_subscription_key or set environment variable BING_SEARCH_API_KEY"
        #     )
        # elif bing_search_api_key:
        #     self.bing_api_key = bing_search_api_key
        # else:
        #     self.bing_api_key = os.environ["BING_SEARCH_API_KEY"]
        # self.endpoint = "https://api.bochaai.com/v1/web-search"
        self.limit = k
        self.webpage_helper = WebPageHelper(
            min_char_count=min_char_count,
            snippet_chunk_size=snippet_chunk_size,
            max_thread_num=webpage_helper_max_threads,
        )
        self.usage = 0

        # If not None, is_valid_source shall be a function that takes a URL and returns a boolean.
        if is_valid_source:
            self.is_valid_source = is_valid_source
        else:
            self.is_valid_source = lambda x: True

    def get_usage_and_reset(self):
        usage = self.usage
        self.usage = 0

        return {"BingSearch": usage}

    def forward(
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = [],
        offset=0, fields=["title", "paperId", "abstract", "isOpenAccess", 'openAccessPdf', "year","publicationDate","citations.title","citations.abstract","citations.isOpenAccess","citations.openAccessPdf","citations.citationCount","citationCount","citations.year"],
                            publicationDate=None, minCitationCount=0, year=None, 
                            publicationTypes=None, fieldsOfStudy=None,
    ):
        """Search with Bing for self.k top passages for query or queries

        Args:
            query_or_queries (Union[str, List[str]]): The query or queries to search for.
            exclude_urls (List[str]): A list of urls to exclude from the search results.

        Returns:
            a list of Dicts, each dict has keys of 'description', 'snippets' (list of strings), 'title', 'url'
        """
        queries = (
            [query_or_queries]
            if isinstance(query_or_queries, str)
            else query_or_queries
        )
        self.usage += len(queries)

        url_to_results = {}

        valid_url_to_snippets = self.webpage_helper.urls_to_snippets(
            ["https://www.mdpi.com/1999-4915/13/12/2414/pdf?version=1640245488"])
        print(valid_url_to_snippets)

        for query in queries:
            try:

                # payload = json.dumps({
                #     "query": query,
                #     **self.params
                # })
                fields=["title", "paperId", "abstract", "isOpenAccess", 'openAccessPdf', "year","publicationDate","citations.title","citations.abstract","citations.isOpenAccess","citations.openAccessPdf","citations.citationCount","citationCount","citations.year"]
                payload = {
                    'query': query,
                    'year': year,
                    "fields": fields,
                    "publication_date_or_year":publicationDate,
                    "min_citation_count":minCitationCount,
                    "limit":self.limit,
                    "publication_types":publicationTypes,
                    "fields_of_study":fieldsOfStudy
                }

                sch = SemanticScholar()
                response = sch.search_paper(**payload)
                # url,title,abstract
                for d in response:
                    if self.is_valid_source(d["url"]) and d["url"] not in exclude_urls:
                        url_to_results[d["url"]] = {
                            "url": d["url"],
                            "title": d["name"],
                            "description": d["snippet"],
                        }
            except Exception as e:
                logging.error(f"Error occurs when searching query {query}: {e}")

        valid_url_to_snippets = self.webpage_helper.urls_to_snippets(
            list(url_to_results.keys())
        )
        collected_results = []
        for url in valid_url_to_snippets:
            r = url_to_results[url]
            r["snippets"] = valid_url_to_snippets[url]["snippets"]
            collected_results.append(r)

        return collected_results
    
if __name__ == "__main__": 
    
    rs = ScholarSearch(k=3)
    rs.forward("What is the capital of France?")
    print(rs)