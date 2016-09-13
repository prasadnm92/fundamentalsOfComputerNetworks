# WEBCRAWLER

## High-level Approach:

I have used the BFS method of traversal to crawl through all the links of the **fakebook** website. Considering each webpage as a node and the links in that page as the children of that node, we traverse through the tree using BFS traversal searching for secrets (in the h2 tags).

Since the aim of the project is to traverse only webpages of **fakebook**, the northeastern home page ("http://www.northeastern.edu"), the professor's page ("http://www.ccs.neu.edu/home/choffnes/") and the link to mail the professor ("mailto:choffnes@ccs.neu.edu") are all considered as *traversed* so that my crawler does not visit these links.

Challenges faced:

Understanding how the website authenticates the users and how each page can be retreived fastly required some study of the website source pages. Parsing the pages for easy retrieval of required data was also a challenge to make it unambiguous. Also, keeping the code as modular as possible was a challenge.

Testing:

By running the program multiple times, almost all errors with respect to the http status codes were observed and rectified. I handled all the errors that we could think of intuitively.
