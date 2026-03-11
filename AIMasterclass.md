Restaurant owners have to search from a wide variety of sources to get competitor intelligence in their locality inorder to plan and price well. I built a system to solve that. 

This system scrapes data from 37,000+ restaurant websites, processes it through an ETL pipeline, and stores it in a graph database I designed from scratch. A conversational chatbot frontend sits on top, powered by an agentic AI backend using a planner-executor pattern that routes user queries to predefined tools. The live link is in the main README.md of this repo. Expect 20 to 40s cold start delay as backend wakes from sleep. Here are some decisions I made in the project:-
    • Designed the graph ontology from scratch.
    • Implemented threading operations and cypher query optimisation that reduced the database load times from 26 minutes to 7 minutes.
    • Designed the ETL pipeline as a horizontal (scraping) and vertical (loading) scaleable system.
    • Designed the RAG system to run async with thread_id to keep conversation states isolated. 
    • Hard code the cypher queries to reduce token cost, keeping queries deterministic, reduce hallucination and avoid having to finetune a model to generate cypher queries. 
    • Used a large and small model from Groq for good reasoning and simple tool calls.

I built the application but I want to go deeper into fundamentals so that I have more freedom and control over what the system can achieve. I want to know what is really going on when a model reasons versus when it pattern-matches. Right now I am making engineering decisions by intuition and reading papers I only half-understand. I want to reach the point where I can make those decisions from first principles. Most courses optimise for scale but AI Masterclass optimises for depth. That is exactly the environment I need to build genuine understanding rather than surface familiarity. The track record of the alumni speaks for itself.

My goal is to build my own company, a SaaS product combining AI and computer vision. I cannot do that confidently on borrowed understanding. I need to own the fundamentals.

Additionally, I wish to share a story of how quickly I can learn. Back in December 2020, I had enrolled at CADD center to learn a software called CATIA 3D which is a 3D modeling software that is used to design cars, aeroplanes, etc. Its a 3 month course that I was able to finish in 1.5 months. During the initial days, I was struggling to understand the intuition behind the sequence of operations and my teachers thought I was stupid. After a week, I was able to grasp the concepts and quickly finish the exercises. I was the only one who finished the entire exercise book. For my capstone project, I decided to build a 7 cylinder radial engine which is very large and complex to really push my limits. It took me 2 weeks and when I showed it to my teachers, they were blown away. One of the teachers complemented me saying that even they couldnt have made such a thing. Here is a link to that [model](https://grabcad.com/library/7-cylinder-radial-engine-8).


I've already shipped a production agentic AI system. Now I want to understand how it actually works under the hood.
