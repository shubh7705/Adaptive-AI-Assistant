from AdaptiveChat import AdaptiveChat

chat = AdaptiveChat()

# query = f"""
#   Summerize the folllowing text

# Microsoft and NVIDIA Redefined Windows for the Agentic Era
# The future of personal computing is shifting from app-centric interactions to agent-centric systems, where AI-powered Windows PCs can reason, act, and complete complex tasks locally through tightly integrated hardware, operating systems, and secure agent runtimes.
# 8 mins read
# Jun 08, 2026
# Share
# The personal computer industry is undergoing its most profound structural evolution in forty years. For decades, the fundamental human-computer interface was transactional: users launched applications, typed commands, and clicked menu buttons to complete tasks. Today, Microsoft and NVIDIA are completely rewriting that contract.

# By merging enterprise-grade silicon architectures with deep operating system integrations, the two giants are transforming the Windows PC from a passive, app-launching tool into an active, autonomous teammate. Unveiled through sweeping announcements at COMPUTEX 2026 and Microsoft Build 2026, the new NVIDIA RTX Spark platform and the Windows Agent-Native Runtime represent a hardware and software shift that fundamentally redefines client computing.

# """

query = input("Ask any question?")

print(chat.ask(query))