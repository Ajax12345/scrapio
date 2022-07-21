# Scrapio

This repo contains the source of several different web data extraction algorithms, originally designed to be used in conjuction with each other, but will also work as standalone miners. 

## Key Source File Directory

| File | Description |
|------|-------------|
|[tree_matcher.py](https://github.com/Ajax12345/scrapio/blob/main/scrapio/tree_matcher.py)| An adaption of Liu and Zhai's partial tree alignment algorithm [[1](https://github.com/Ajax12345/scrapio/edit/main/README.md#references)], with several important modifications. Used for detecting structured content with few definitive HTML element attributes |


## References

1. Liu, B., & Zhai, Y. (2005, May 10-14). Web data extraction based on partial tree alignment. *Proceedings of the 14th international conference on World Wide Web, WWW 2005, Chiba, Japan.* https://dl.acm.org/doi/10.1145/1060745.1060761
