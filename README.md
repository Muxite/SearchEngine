# SearchApe
A basic search engine using async webscrapers. It is not finished yet.

The structure revolves around going to a website, determining the key terms of the webpage, then collecting all the links.
The scrapers will then go to the links, and repeat the process, eventually indexing a large part of the website. 
The app uses a lot of containers, with Redis as the cache, and MySQL as the storage. 
I am investigating using llama.cpp to improve the tagging system by using AI. 
