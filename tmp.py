import dspy
from typing import Callable, Union, List
from knowledge_storm.sementic_search import SementicSearcher
import logging
import json
from typing import List, Union
import scipdf
from knowledge_storm.utils import WebPageHelper
import requests 
import os

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

        self.endpoint = "https://api.bochaai.com/v1/web-search"
        self.params = {"summary": True, "count": k, "page": 1}
        self.webpage_helper = WebPageHelper(
            min_char_count=min_char_count,
            snippet_chunk_size=snippet_chunk_size,
            max_thread_num=webpage_helper_max_threads,
        )
        self.usage = 0
        self.reader = SementicSearcher(save_file = "tmp_file/",ban_paper = [],grobid_url="http://223.99.170.187:8070")
        self.limit = k


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
        self, query_or_queries: Union[str, List[str]], exclude_urls: List[str] = []
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

        for query in queries:
            try:
                # paper: list of Result objects
                papers = self.reader.search_(query,self.limit)
                for paper in papers:
                    url = paper.url
                    if self.is_valid_source(url) and url not in exclude_urls:
                        url_to_results[url] = {
                            "url": url,
                            "title": paper.title,
                            "description": paper.abstract,
                            "sections": paper.article["sections"],
                        }
            except Exception as e:
                logging.error(f"Error occurs when searching query {query}: {e}")

        valid_url_to_snippets = self.webpage_helper.article_to_snippets(url_to_results)
        
        collected_results = []
        for url in valid_url_to_snippets:
            r = url_to_results[url]
            r["snippets"] = valid_url_to_snippets[url]["snippets"]
            collected_results.append(r)

        return collected_results
    
if __name__ == "__main__": 
    
    rs = ScholarSearch(k=3)
    rs.forward("flux pinning")
    print(rs)