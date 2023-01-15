# Scrapio

Scrapio is a suite of automatic web content extractors, largely designed to pull structured and semi-structured web page content (for example, news articles and tables).

This repo contains the source of several different web data extraction algorithms, originally designed to be used in conjuction with each other, but will also work as standalone page record miners. 

## Key Source File Directory

| File | Description |
|------|-------------|
|[`tree_matcher.py`](https://github.com/Ajax12345/scrapio/blob/main/scrapio/tree_matcher.py)| An adaption of Liu and Zhai's partial tree alignment algorithm [[1](https://github.com/Ajax12345/scrapio/edit/main/README.md#references)], with several important modifications. Used for detecting structured content with few definitive HTML element attributes |
|[`tree_traversal2.py`](https://github.com/Ajax12345/scrapio/blob/main/scrapio/tree_traversal2.py)| Custom element record detection, based on tag pattern matching and similar element attribute grouping |
| [`tree_merger.py`](https://github.com/Ajax12345/scrapio/blob/main/scrapio/tree_merger.py) | Performs removal of extraneous and irrelevant HTML page content, such as headers, footers, etc. |
| [`tree_converter_handlers3.py`](https://github.com/Ajax12345/scrapio/blob/main/scrapio/tree_converter_handlers3.py) | Converts large similar record objects, ultimately generated by the preceding files, into two dimensional `JSON` objects for export later |

## References

1. Liu, B., & Zhai, Y. (2005, May 10-14). Web data extraction based on partial tree alignment. *Proceedings of the 14th international conference on World Wide Web, WWW 2005, Chiba, Japan.* https://dl.acm.org/doi/10.1145/1060745.1060761
