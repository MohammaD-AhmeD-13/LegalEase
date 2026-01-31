ABSTRACT
Getting professional legal help in Pakistan is often difficult due to high costs, linguistic barriers, and the complexity of procedural terminology, leaving individuals, freelancers, and Small-to-Medium Enterprises (SMEs) vulnerable to legal risks. To address this gap, this project presents LegalEase, an AI-powered bilingual legal assistant designed to make civil and commercial legal support available to everyone. Using Natural Language Processing (NLP) and Large Language Models (LLMs), the system provides a user-friendly web interface that helps users understand legal documents more easily. The system offers a comprehensive suite of features, including the automated analysis of contracts to detect risky clauses, the generation of essential legal documents (such as NDAs and affidavits) through dynamic templates, and the summarization of dense legal text into plain Urdu and English. Additionally, LegalEase incorporates a multimodal query engine allowing users to interact via text or voice for context-aware legal guidance. Recognizing the ethical limitations of AI in the legal domain, the system includes a conditional expert referral feature. The system includes an expert referral feature, which connects users to verified professionals for complex queries that require human expertise. Developed using the Incremental Software Process Model, LegalEase aims to reduce dependency on expensive consultations and build a more inclusive, online legal services in Pakistan. 
TABLE OF CONTENTS

CHAPTER 1	13
INTRODUCTION	13
1.1. Background	13
1.2. Introduction	13
1.3. Problem Statement	14
1.4. Objectives	15
1.5. Project Scope	15
1.6. Advantages of the System	16
1.7. Relevance to the Study Program	17
1.8. Chapter Summary	17
CHAPTER 2	18
2.1. EXISTING SYSTEMS	18
2.2. Drawbacks in Existing Systems	18
2.3. Examples of Existing Systems	19
2.3.1 DoNotPay	19
2.3.2 LegalZoom	19
2.3.3 Bahaq Legal AI	19
2.3.4 AI Attorney	19
2.3.5 Wakeel AI	20
2.4. Need to Replace Existing Systems	20
2.5. Chapter Summary	21
CHAPTER 3	22
REQUIREMENT ENGINEERING	22
3.1. Proposed System	22
3.2. Understanding the System	22
3.2.1. User Involvement	23
3.2.2. Stakeholders	23
3.2.3. Domain	24
3.2.4. Needs of System	24
3.2.4.1. Hardware Needs	24
3.2.4.2. Software Needs	25
3.2.4.3. Data Needs	25
3.2.4.4. Security and Privacy Needs	25
3.2.4.5. Performance and Maintenance Needs	25
3.2.5. Functional Requirements	26
3.2.6. Non-Functional Requirements	32
3.3.2.1 Performance	32
3.3.2.2 Scalability	32
3.3.2.3 Security	32
3.3.2.4 Availability	32
3.3.2.5 Usability	32
3.3.2.6 Maintainability	32
3.3.2.7 Reliability	33
3.3.2.8 Compatibility	33
3.3.2.9 Ethical Compliance	33
3.2.7. Requirements Baseline	33
3.2.8. Need to Feature Mapping	33
3.3. Gantt Chart	34
3.4. Hurdles in Optimizing the Current System	35
3.4.1 Data Availability	35
3.4.2 Language and Contextual Complexity	35
3.4.3 Technical Resource Constraints	35
3.4.4 Model Accuracy and Validation	36
3.4.5 Accessibility and Integration	36
3.5. Chapter Summary	36
CHAPTER 4	37
DESIGN	37
4.1. Software Process Model	37
4.1.1 Benefits of Selected Model	37
4.1.2 Limitations of Selected Model	37
4.2. Design	38
4.2.1. Methodology of the LegalEase	38
4.2.2. Entity Relationship Diagram	39
4.2.3. UML Diagrams	40
4.2.3.1. Use Case Diagram of LegalEase	40
4.2.3.2. Class Diagram of LegalEase	41
4.2.3.3. Activity Diagram of LegalEase	42
4.2.3.4. Sequence Diagram of LegalEase	43
4.2.3.5. Component Diagram of LegalEase	44
4.3. Chapter Summary	44
REFERENCES	46

	 
LIST OF FIGURES

FIGURE 3.1 GANTT CHART FOR LEGALEASE	35
FIGURE 4.1 METHODOLOGY DIAGRAM OF LEGALEASE	38
FIGURE 4.2 ENTITY RELATIONSHIP DIAGRAM OF LEGALEASE	39
FIGURE 4.3 USE CASE DIAGRAM OF LEGALEASE	40
FIGURE 4.4 CLASS DIAGRAM OF LEGALEASE	41
FIGURE 4.5 ACTIVITY DIAGRAM OF LEGALEASE	42
FIGURE 4.6 SEQUENCE DIAGRAM OF LEGALEASE	43
FIGURE 4.7 COMPONENT DIAGRAM OF LEGALEASE	44















 
LIST OF TABLES
TABLE 2.1 COMPARISON OF EXISTING SYSTEMS WITH PROPOSED SYSTEM (LEGALEASE)	20
TABLE 3.1 USER NEEDS OF SYSTEM	26
TABLE 3.2 FUNCTIONAL REQUIREMENT 01	27
TABLE 3.3 FUNCTIONAL REQUIREMENT 02	27
TABLE 3.4 FUNCTIONAL REQUIREMENT 03	28
TABLE 3.5 FUNCTIONAL REQUIREMENT 04	28
TABLE 3.6 FUNCTIONAL REQUIREMENT 05	29
TABLE 3.7 FUNCTIONAL REQUIREMENT 06	29
TABLE 3.8 FUNCTIONAL REQUIREMENT 07	30
TABLE 3.9 FUNCTIONAL REQUIREMENT 08	30
TABLE 3.10 FUNCTIONAL REQUIREMENT 09	31
TABLE 3.11 USER NEEDS OF SYSTEM	33
 
Chapter 1 
	INTRODUCTION
1.1. Background
Among the many fields influenced by AI, the legal domain remains one of the most challenging yet promising areas for using technology. Legal work traditionally dependent on extensive human expertise, procedural precision, and interpretation of complex language has begun to experience gradual automation through Natural Language Processing (NLP) and Machine Learning (ML) technologies [1] [2].
The legal system in Pakistan continues to rely on manual documentation, physical consultations, and old-fashioned administrative methods that often make access difficult. For the majority of citizens and small-to-medium enterprises (SMEs), obtaining legal assistance remains expensive, time-consuming, and linguistically inaccessible. Legal contracts and agreements are usually written in highly technical English, filled with terminologies that ordinary people find difficult to interpret. Consequently, individuals frequently sign contracts without fully comprehending their implications exposing themselves to potential exploitation or financial and legal risk.
In recent years, AI-driven language models have demonstrated remarkable capability in understanding, summarizing, and generating human language with contextual accuracy. When applied to the legal domain, these technologies can read documents, detect inconsistencies, and simplify clauses into comprehensible summaries. Furthermore, bilingual NLP systems now enable the translation and explanation of legal concepts in native languages such as Urdu, breaking linguistic barriers and ensuring inclusivity for non-English-speaking populations.
LegalEase aims to solve the accessibility problem within Pakistan’s legal framework by developing an AI-powered legal assistant. The system integrates the strengths of NLP and Large Language Models (LLMs) to review, summarize, and generate legal documents while offering bilingual support in Urdu and English.
1.2. Introduction
The growing demand for accessible and technology-driven legal assistance has given rise to the concept of AI legal assistants, intelligent systems capable of interpreting and processing legal texts automatically. LegalEase builds upon this concept by developing a localized, bilingual, and data-driven platform tailored to the legal conditions in Pakistan.
The project operates at the intersection of Data Science, Natural Language Processing, and Law, utilizing pre-trained LLMs to extract meaning from complex legal documents. The system enables users to:
	Upload and review contracts to identify key clauses and potential risks.
	Generate legal documents such as NDAs, affidavits, and service agreements through guided inputs.
	Summarize legal text in plain, understandable Urdu or English.
	Communicate with an AI Assistant for contextual legal queries. 
LegalEase introduces a freemium service model, providing essential features like document summaries and consultations at no cost, while premium users can access advanced analytics, full contract reviews, and professional referrals. In short, LegalEase aims to change how ordinary users interact with legal information, reducing dependency on costly legal professionals and promoting an equitable approach to justice through technology.
1.3. Problem Statement
Legal documentation and consultation in Pakistan face numerous obstacles, inaccessibility, high costs, linguistic barriers, and legal complexity [3]. These issues collectively hinder individuals and small businesses from obtaining professional legal assistance. As a result, many are left vulnerable to exploitation and uninformed decision-making in matters that have long-term legal and financial consequences.
“There is no localized, AI-driven legal assistant capable of performing document review, risk identification, and document generation aligned with Pakistani law and bilingual linguistic needs.”
This gap persists despite the rapid growth of global LegalTech platforms such as LawDepot, Rocket Lawyer, and DoNotPay, which are mostly made for Western laws and thus fail to address Pakistan’s unique legal frameworks and linguistic diversity. Furthermore, legal documents such as contracts, memoranda, and agreements are often written in dense legal English, making them incomprehensible to non-experts. Consequently, freelancers and small enterprises frequently operate without a clear understanding of their legal obligations, resulting in disputes and unfair terms.
LegalEase aims to bridge this gap by developing an AI-powered solution that uses natural language processing (NLP), machine learning, and bilingual interface design to make legal understanding accessible to everyone.
1.4. Objectives
The primary objective of LegalEase is to design and develop an intelligent, bilingual legal assistant that uses Natural Language Processing (NLP) and Machine Learning (ML) to provide automated legal guidance aligned with Pakistani civil law. The system aims to make legal information accessible, affordable, and comprehensible for the general public and SMEs.
Specifically, the project seeks to: 
❖ Develop an AI-powered assistant capable of addressing legal, tax, and finance-related queries in Urdu and English.
❖ Automate the generation of essential legal documents such as NDAs, affidavits, and service agreements through customizable templates.
❖ Implement an intelligent contract analysis module that identifies risky clauses, missing terms, and inconsistencies.
❖ Integrate a plain-language summarization engine that converts complex legal text into easy-to-understand explanations.
❖ Introduce an expert referral feature that connects users with verified legal professionals when AI-generated guidance is insufficient.
Collectively, these objectives reflect LegalEase’s broader mission to democratize legal knowledge, reduce reliance on expensive consultations, and promote digital access in Pakistan’s legal system.
1.5. Project Scope
LegalEase focuses on delivering an AI-driven bilingual legal assistant that simplifies legal understanding and document management for individuals, freelancers, and small-to-medium enterprises in Pakistan. The project’s scope emphasizes accessibility, automation, and secure interaction through a web-based platform powered by Natural Language Processing and Machine Learning.
The system’s key functional areas include:
	User Authentication and Profiles: Secure sign-up, login, and profile management to personalize user access and document storage.
	Document Upload and Management: Uploading, organizing, and securely storing contracts or legal files in encrypted form.
	Contract Review and Risk Detection: Automatic analysis of uploaded documents to highlight risky clauses, missing terms, and potential liabilities.
	Legal Document Generation: Dynamic creation of essential documents such as NDAs, affidavits, and service agreements using guided templates.
	Bilingual Summarization and Translation: Simplifying complex legal text into clear Urdu or English explanations.
	Voice Interaction: Allowing users to input queries through speech for hands-free communication.
	Expert Referral System: Connecting users with verified legal professionals when AI-generated advice is insufficient.
	Data Security and Privacy: Encrypting all stored information and maintaining user confidentiality in compliance with ethical standards.
1.6. Advantages of the System
LegalEase introduces several practical benefits that strengthen its relevance and impact within Pakistan’s digital transformation landscape:
	Accessibility: Offers continuous access to bilingual legal assistance, enabling individuals and SMEs to obtain support without geographical or linguistic constraints.
	Accuracy and Consistency: Utilizes a structured, law-aligned knowledge base that ensures guidance remains compliant with Pakistani civil law.
	Convenience: Allows users to generate, review, and summarize legal documents directly through an intuitive web interface.
	Scalability: Designed for expansion into new legal domains, such as criminal law and potential integration with government e-services in the future.
1.7. Relevance to the Study Program
This project is directly aligned with the principles and learning outcomes of the BS in Data Science program. It bridges academic theory and societal application by combining core areas such as machine learning, data management, and natural language processing.
Through the development of LegalEase, students apply advanced AI concepts to a real-world domain that requires both technical precision and ethical responsibility. The system exemplifies how intelligent algorithms can be applied to improve access to justice, automate language understanding, and enhance decision-making processes in sensitive, data-driven contexts.
In essence, LegalEase shows how AI can move from theory to meaningful impact by helping people understand and manage legal matters with clarity and confidence.
1.8. Chapter Summary
This chapter introduced LegalEase and established the motivation behind its development. It described how recent advances in NLP and pre-trained language models enable practical automation in the legal domain, and why Pakistan’s socio-legal context urgently needs an accessible, bilingual solution. The chapter outlined clear objectives for LegalEase: to provide an AI-powered Urdu/English Legal Assistant, automate common legal documents, offer contract risk analysis, generate plain-language summaries, and refer complex cases to verified professionals. The project scope was defined to focus on civil and commercial legal assistance for individuals and SMEs, with explicit exclusions for criminal representation and courtroom advocacy. Finally, the chapter highlighted the system’s advantages and its direct relevance to the Data Science and curriculum, positioning LegalEase as a feasible, ethically minded, and impactful Legal-Tech prototype.

 
Chapter 2 
	EXISTING SYSTEMS

2.1. EXISTING SYSTEMS
Across global and local markets, several LegalTech platforms show how technology can make legal work easier such as document drafting, case research, and client consultation. However, most existing systems either serve Western jurisdictions or focus on professional users, leaving a gap in accessibility, affordability, and bilingual usability for Pakistan’s general population.
2.2. Drawbacks in Existing Systems
Despite notable progress in global and local LegalTech innovation, the existing solutions still fall short of meeting the diverse needs of users in Pakistan. Most platforms focus on helping legal professionals or operate within foreign legal frameworks, offering limited practical value to ordinary citizens or small enterprises.
Nearly all available tools present legal content exclusively in English, making them inaccessible to a large segment of the population more comfortable with Urdu or regional languages. Similarly, personalization remains minimal, current systems provide generic templates or predefined workflows that fail to account for the user’s specific legal situation or local jurisdictional nuances.
Another critical limitation is the absence of intelligent contract analysis. Existing tools may assist with form-filling or basic drafting, but few possess the capability to automatically identify risky clauses, inconsistencies, or obligations that could expose a user to legal or financial harm. In addition, many platforms function as static information repositories rather than interactive assistants. They rely on the user to know what to search for, rather than guiding them through an adaptive, question-based experience.
Lastly, integration with professional legal support is often missing. Users encountering complex issues have no structured pathway to escalate their query or connect with certified legal experts for validation. This disconnect between automated tools and human expertise limits the trust and reliability of these systems in real-world decision-making.
Collectively, these drawbacks reveal a significant gap between the availability of digital legal resources and their ability to deliver meaningful, context-aware assistance to Pakistani users.
2.3. Examples of Existing Systems
Several international and local LegalTech systems illustrate the difference between current capabilities and what LegalEase aims to deliver:
2.3.1 DoNotPay
DoNotPay is an AI-based platform that automates routine legal processes such as appealing fines or drafting letters. While it popularized AI-assisted legal automation, it is limited to Western jurisdictions and lacks localization for South Asian legal systems.
2.3.2 LegalZoom
LegalZoom enables online document creation and company registration through guided templates. It simplifies document generation but is restricted to U.S. law and does not include adaptive AI review or multilingual support.
2.3.3 Bahaq Legal AI
Bahaq is a Pakistani AI legal assistant offering document drafting and research tools aligned with local laws. However, it is designed primarily for lawyers and legal professionals, offering limited accessibility and plain-language guidance for non-expert users.
2.3.4 AI Attorney
AI Attorney provides AI-driven document drafting, clause detection, and legal consultation services within Pakistan. It represents the most direct local competitor to LegalEase, but it primarily replicates Western LegalTech workflows and lacks Urdu-language interaction, personalized clause explanations, and deep contextual alignment with Pakistan’s legal ecosystem.
2.3.5 Wakeel AI
Wakeel AI integrates document management, research, and collaboration tools for law firms. Although it incorporates AI-assisted features, it focuses on professional case workflows rather than simplified, user-facing automation for the public.
2.4. Need to Replace Existing Systems
The limitations of current solutions highlight the need for a localized, intelligent, and bilingual legal platform. Pakistan’s legal ecosystem requires a system that merges document automation, clause-level risk analysis, and plain-language summarization within a single interface.
LegalEase fulfills this need by offering:
	AI-based document creation and risk review aligned with Pakistani law.
	Dual-language (Urdu and English) interaction.
	Simplified explanations of legal clauses for ordinary users.
	Secure data management and escalation to verified professionals for complex cases.
By combining these capabilities, LegalEase bridges the gap between automated legal tools and local accessibility, representing a significant advancement toward inclusive LegalTech in Pakistan.
Table 2.1 Comparison of Existing Systems with Proposed System (LegalEase)
Feature	DoNotPay	LegalZoom	Bahaq AI	AI Attorney	Wakeel AI	LegalEase (Proposed)
Jurisdiction	US / UK	US	PK	PK	PK	PK
Language Support	English	English	English	English	English	Urdu + English
AI Integration	Basic	Minimal	Moderate	High	Moderate	Advanced (NLP)
Document Generation					Limited	
Document Review	🗙	🗙	Limited	🗙	🗙	 Automated
Risk Detection	🗙	🗙	Partial	Basic	🗙	 Clause-level
Summarization	🗙	🗙	Limited	🗙	🗙	 Bilingual
User Guidance	Guided	Templates	Complex	Limited	🗙	 Interactive
Target Users	Public	SMEs	Lawyers	Public	Law firms	Public, SMEs, Freelancers
Professional Integration	🗙	🗙		🗙		 Referral-based
Local Legal Alignment	🗙	🗙				 Full Compliance
Accessibility	Region-limited	Paid			Enterprise	 Freemium, Open
2.5. Chapter Summary
This chapter analyzed existing legal automation tools both globally and locally. International platforms like DoNotPay and LegalZoom have shown how AI can simplify legal processes but remain limited to Western legal contexts. Local solutions such as AI Attorney, Bahaq, and Wakeel AI demonstrate progress toward digital transformation yet fail to deliver comprehensive bilingual accessibility or plain-language assistance. These shortcomings reveal a persistent gap between the availability of legal technology and its practical usability for ordinary Pakistani users. LegalEase aims to close this gap through localized AI integration, bilingual comprehension, and context-aware document review, ultimately making legal help easier to understand and use and automation within Pakistan’s socio-legal framework.

 
Chapter 3 
	REQUIREMENT ENGINEERING
3.1. Proposed System 
LegalEase is a bilingual, AI-powered legal assistant developed to make legal understanding and document management more accessible to individuals, freelancers, and small-to-medium enterprises in Pakistan. The system leverages Natural Language Processing (NLP) and Machine Learning (ML) to automatically analyze, simplify, and generate legal documents in both English and Urdu.
Unlike traditional legal websites or static repositories, LegalEase functions as an interactive assistant capable of reviewing uploaded contracts, detecting risky or missing clauses, and providing plain-language explanations for non-experts. It also includes guided templates for generating common legal documents such as Non-Disclosure Agreements (NDAs), service agreements, and affidavits.
The platform follows a freemium model, offering essential document analysis and summaries for free, while premium users can access advanced features such as detailed risk scoring, clause benchmarking, and professional referral services. The system aims to bridge the accessibility gap in Pakistan’s legal ecosystem by combining data-driven intelligence, bilingual communication, and an intuitive interface.
3.2. Understanding the System
LegalEase is designed around three core principles: accessibility, accuracy, and adaptability. It is intended not only to automate routine legal work but also to help users understand the legal implications of their actions in a clear and inclusive manner.
At its core, the system integrates the following modules:
	Document Analysis Module: Uses NLP to parse and interpret uploaded contracts, highlight risky clauses, and provide plain-language explanations.
	Document Generation Module: Generates legal templates and drafts based on user input.
	Summarization and Translation Module: Converts complex legal text into concise Urdu or English summaries.
	Consultation and Referral Module: Allows users to ask legal questions or connect with verified lawyers when AI confidence is low.
Together, these components form an ecosystem that simplifies legal work while maintaining compliance with Pakistan’s civil and commercial laws.
3.2.1. User Involvement
LegalEase was designed with active consideration of its end users. The primary user groups include:
	Individuals and freelancers who frequently sign contracts without understanding legal implications.
	Small and medium enterprises (SMEs) that require quick, affordable document drafting and review.
	Students and professionals who wish to learn about legal processes in simple, bilingual terms.
User involvement occurs at multiple stages of system development. During early prototypes, test users provide feedback on language clarity, feature usability, and risk detection accuracy. This user-driven approach ensures that the system remains practical, inclusive, and easy to navigate even for non-technical audiences.
3.2.2. Stakeholders 
LegalEase involves several key stakeholders:
	End Users: Individuals, freelancers, and SMEs who use the platform for document creation and review.
	Legal Professionals: Verified lawyers who may collaborate for consultation or validation services.
	System Developers: We (Ahmed & Hassan) will be responsible for maintaining NLP models and system architecture.
	Supervisory Authority / Academic Advisors: Supervisor Mr. Safdar Hussain ensuring technical accuracy, ethics, and compliance with research standards.
	Regulatory Bodies: Legal and data protection authorities whose frameworks guide the system’s ethical and legal compliance.
3.2.3. Domain 
The system operates within the LegalTech domain, specifically focusing on civil and commercial law in Pakistan. LegalEase uses Data Science and NLP to interpret legal text and provide insights to users without requiring professional legal literacy.
The domain intersects with several technical and legal disciplines:
	Artificial Intelligence (AI): Enables document understanding and automation.
	Natural Language Processing (NLP): Facilitates bilingual text interpretation and summarization.
	Data Management: Ensures secure storage and retrieval of legal documents.
	Legal Studies: Provides the framework for compliant document structure and analysis.
By situating itself within this interdisciplinary domain, LegalEase contributes to Pakistan’s growing LegalTech landscape and demonstrates how AI can enhance public access to justice.
3.2.4. Needs of System
To function effectively and deliver accurate, bilingual legal assistance, LegalEase requires a combination of technical, data, and operational components. These needs ensure system stability, scalability, and legal reliability.
3.2.4.1. Hardware Needs
	A computer or server with a multi-core processor and sufficient GPU/CPU capacity for running AI and NLP models efficiently.
	Minimum 16 GB RAM for real-time language processing.
	Secure storage infrastructure for managing user-uploaded legal documents and system-generated outputs.
	Reliable internet connectivity for cloud-based model integration and updates.
3.2.4.2. Software Needs
	Programming Environment: Python (for NLP, AI, and backend logic).
	Frameworks and Libraries: TensorFlow/Keras for model development, Hugging Face Transformers for LLM integration, and NLTK/spaCy for language processing.
	Database: MySQL or PostgreSQL for structured data management (user profiles, document metadata).
	Web Framework: Django or Flask for backend web development.
	Frontend Tools: HTML, CSS, JavaScript, and Bootstrap for an intuitive user interface.
	Integrations: Whisper or SpeechRecognition for voice input, and bilingual support.
3.2.4.3. Data Needs
	A curated dataset of Pakistani legal documents, contract templates, and legislative texts for model fine-tuning.
	Legal dictionaries, Urdu-English bilingual corpora, and clause-specific annotations to enhance comprehension and translation accuracy.
	Data cleaning and labeling mechanisms to ensure contextual relevance and remove redundant or outdated entries.
3.2.4.4. Security and Privacy Needs
	End-to-end encryption for document uploads and storage.
	Authentication mechanisms (user login and session management) to protect sensitive information.
	Regular database backups and secure data retrieval protocols.
	Compliance with ethical and privacy standards for handling legal content.
3.2.4.5. Performance and Maintenance Needs
	Optimization of NLP pipelines for faster clause detection and summarization.
	Logging and monitoring systems to track model accuracy, server health, and user interactions.
	Routine updates to incorporate new laws, templates, and model improvements.
	Scalability provisions for supporting an increasing number of users over time.
SR #	Needs	Need ID
1.	Plain-language explanations for legal text	NI-01
2.	Quick contract risk checking	NI-02
3.	Legal document and template generation	NI-03
4.	Obligation and deadline tracking	NI-04
5.	Voice and Urdu-based interaction	NI-05
6.	Educational explanations of legal clauses	NI-06
7.	Lawyer verification and review support	NI-07
8.	Secure data management and user privacy	NI-08
Table 3.1 User Needs of System
Requirement Engineering defines and documents the functionalities, constraints, and performance expectations of the proposed system. For LegalEase, this process ensures that every system component aligns with the project’s objectives — providing accurate, secure, and bilingual AI-based legal assistance within Pakistan’s civil and commercial context.
The requirements are divided into Functional and Non-Functional categories to represent both the behavioral and operational needs of the system.
3.2.5. Functional Requirements
Functional requirements describe the specific actions and services the system must perform to achieve its goals. These requirements directly reflect the features and user interactions that LegalEase supports.
	
Table 3.2 Functional Requirement 01
Functional Requirement ID	FR-01
Name	User Authentication
Description	Allows users to sign up, log in, and manage their profiles securely.
Input	Username, Password
Output	User session token
Precondition	User account must exist
Postcondition	User authenticated and granted access

Table 3.3 Functional Requirement 02
Functional Requirement ID	FR-02
Name	Document Upload
Description	Enables users to upload legal documents (PDF/DOCX) for analysis.
Input	Document file
Output	Parsed text stored in system
Precondition	User must be logged in
Postcondition	Document ready for processing

Table 3.4 Functional Requirement 03
Functional Requirement ID	FR-03
Name	Contract Analysis
Description	Processes uploaded documents using NLP to detect risky clauses and potential risks.
Input	Uploaded text
Output	Highlighted clauses and risk report
Precondition	Document available in system
Postcondition	Risk analysis displayed to user

Table 3.5 Functional Requirement 04
Functional Requirement ID	FR-04
Name	Document Generation
Description	Allows users to generate legal templates (e.g., NDAs, agreements) through guided inputs.
Input	User-provided details
Output	Generated legal document
Precondition	User logged in
Postcondition	Document ready for download

Table 3.6 Functional Requirement 05
Functional Requirement ID	FR-05
Name	Text Summarization
Description	Converts complex legal content into simplified Urdu or English summaries.
Input	Legal text
Output	Simplified bilingual summary
Precondition	Legal document provided
Postcondition	Summary displayed to user

Table 3.7 Functional Requirement 06
Functional Requirement ID	FR-06
Name	Bilingual Translation
Description	Supports interaction and output in both Urdu and English.
Input	User text
Output	Translated Text
Precondition	Input Provided
Postcondition	Translation Displayed

Table 3.8 Functional Requirement 07
Functional Requirement ID	FR-07
Name	Voice Interaction
Description	Enables users to input queries through speech using voice recognition.
Input	Voice input
Output	Transcribed query text
Precondition	Microphone access granted
Postcondition	Query processed by AI module

Table 3.9 Functional Requirement 08
Functional Requirement ID	FR-08
Name	Expert Referral
Description	Connects users with verified lawyers when asked by the user or when the advice alone isn’t enough.
Input	User request
Output	Contact link or referral details
Precondition	User logged in
Postcondition	Referral generated

Table 3.10 Functional Requirement 09
Functional Requirement ID	FR-09
Name	Data Management
Description	Stores, retrieves, and secures user profiles, queries, and document history.
Input	User data
Output	Structured database entries
Precondition	User interacts with system
Postcondition	Data securely updated

3.2.6. Non-Functional Requirements
These factors ensure that LegalEase operates efficiently, remains secure, and provides a smooth experience to all users.
3.3.2.1 Performance
The system should process and analyze a standard legal document within 10–15 seconds to maintain responsiveness and ensure smooth interaction.
3.3.2.2 Scalability
LegalEase must be capable of handling an increasing number of users and larger datasets without a drop in performance or accuracy.
3.3.2.3 Security
All user data and uploaded documents must be encrypted during storage and transmission. Strong authentication mechanisms should prevent unauthorized access.
3.3.2.4 Availability
The platform should maintain maximum uptime to ensure users can access its services reliably at all times.
3.3.2.5 Usability
The interface must be simple, intuitive, and bilingual (Urdu and English) so that users from both legal and non-legal backgrounds can easily navigate it.
3.3.2.6 Maintainability
The system should allow easy updates to laws, document templates, and AI models without major code or service disruptions.
3.3.2.7 Reliability
LegalEase should maintain consistent functionality and achieve at least 90% accuracy in clause detection, summarization, and translation tasks.
3.3.2.8 Compatibility
The application must function smoothly across major web browsers and mobile devices, ensuring accessibility on different platforms.
3.3.2.9 Ethical Compliance
The system should provide legal assistance without offering binding legal advice, including clear disclaimers about the AI’s role and limitations.
3.2.7. Requirements Baseline
The requirements baseline represents the finalized set of functional and non-functional requirements that guide the system’s design and implementation. It ensures that all defined features are developed according to the approved project objectives and within the available constraints.
3.2.8. Need to Feature Mapping
This mapping connects the system needs (defined in Section 3.2.4) with the features and functionalities implemented to meet them. It ensures that every technical or operational need contributes directly to the final system behavior.
Table 3.11 User Needs of System
System Need	Corresponding Feature / Module	Purpose / Outcome
Hardware resources (GPU/CPU, storage)	AI & NLP Processing Module	Enables real-time document analysis and summarization.
Software frameworks (Python, TensorFlow, Django)	Core Backend System	Supports model execution, web logic, and data management.
Bilingual datasets (Urdu-English)	Translation & Summarization Module	Provides accurate bilingual understanding and content generation.
Security and encryption protocols	Authentication & Data Protection Module	Safeguards user data and ensures privacy compliance.
Legal datasets and clause repositories	Risk Detection Engine	Detects high-risk clauses and suggests revisions.
Performance optimization	Model Optimization & Cache System	Reduces latency in analysis and document generation.
Logging and monitoring tools	Admin Dashboard	Tracks model accuracy, usage, and system health.
Scalability infrastructure	Cloud Deployment	Allows expansion as the number of users grows.

3.3. Gantt Chart
The project is planned to be developed in multiple phases, starting from requirement analysis to testing and final documentation. The following Gantt chart presents the proposed timeline for the LegalEase system, outlining each major phase and its estimated duration.
It is important to note that the timeline represents an initial academic projection and may vary depending on available resources, technical challenges, and data accessibility. Since this project will be implemented in the upcoming semester, the actual development period may extend beyond the planned schedule due to limited computational resources and time constraints.
 
Figure 3.1 Gantt Chart for LegalEase
3.4. Hurdles in Optimizing the Current System
3.4.1 Data Availability
There is a shortage of Pakistan-specific legal datasets. It is difficult to find verified local laws in digital formats, and much of the existing legal text is unorganized and needs to be structured before it can be used.
3.4.2 Language and Contextual Complexity
Interpreting text in two languages (English and Urdu) is challenging [4]. Legal phrasing is often very different from standard translation datasets, making it hard for the AI to understand the context.
3.4.3 Technical Resource Constraints
We face limits on computational power and cloud costs. This is a significant challenge because training NLP models requires expensive hardware and we lack open, labeled local datasets.
3.4.4 Model Accuracy and Validation
Ensuring the system is accurate is difficult due to potential bias in pretrained models. Verifying that the AI's legal reasoning is correct is challenging, as is validating the results against the judgment of real legal experts. Since legal advice requires high precision, any "hallucinations" (errors) by the AI could lead to serious consequences for the user.
3.4.5 Accessibility and Integration
Integrating the AI system with a secure, user-facing platform presents several challenges. We must ensure the system is easy to use for people with low technical literacy while strictly maintaining data protection and privacy. Hosting large language models also requires significant backend resources, which can make real-time responsiveness difficult to achieve on a web platform.
3.5. Chapter Summary
This chapter presented a detailed overview of the proposed LegalEase system, including its objectives, functional structure, and development roadmap. It outlined the system’s core requirements, both functional and non-functional, and illustrated its implementation plan through the Gantt chart. Furthermore, it discussed the technical, linguistic, and infrastructural hurdles encountered in optimizing AI-driven legal assistance for Pakistan. Overall, this chapter forms the foundation for understanding the system’s design, challenges, and the practical constraints that guide its ongoing development.


 
Chapter 4 
	DESIGN
4.1. Software Process Model
LegalEase follows the Incremental Software Development Model, which divides the project into manageable modules developed and delivered in stages. Each increment adds new functionality while making sure that previously developed components remain stable and integrated. This approach suits our requirements better because the features, such as contract analysis, summarization, and expert referral can be built, tested, and improved independently before full system integration.
4.1.1 Benefits of Selected Model
	Modularity: Allows separate development of core modules such as document analysis, text summarization, and authentication, ensuring manageable complexity.
	Early Feedback: Each completed increment can be demonstrated for validation, ensuring alignment with functional requirements.
	Reduced Risk: Problems in one module do not stop progress in others, lowering overall development risk.
	Ease of Maintenance: Updates to AI models, templates, or UI elements can be implemented incrementally without affecting the entire system.
4.1.2 Limitations of Selected Model
	Integration Challenges: Combining independently developed modules may lead to compatibility issues during later stages.
	Dependency Management: Changes in one component (e.g., NLP engine) can impact other modules that rely on shared data structures.
	Resource Requirements: Continuous testing and integration across increments can increase development time and technical overhead.
	Incomplete Early Versions: Initial releases may not provide full functionality, requiring users to wait for later increments for a complete experience.
4.2. Design
4.2.1. Methodology of the LegalEase
 
Figure 4.1 Methodology Diagram of LegalEase
4.2.2. Entity Relationship Diagram
 
Figure 4.2 Entity Relationship Diagram of LegalEase
4.2.3. UML Diagrams
4.2.3.1. Use Case Diagram of LegalEase
 
Figure 4.3 Use Case Diagram of LegalEase
4.2.3.2. Class Diagram of LegalEase
 
Figure 4.4 Class Diagram of LegalEase
4.2.3.3. Activity Diagram of LegalEase
 
Figure 4.5 Activity Diagram of LegalEase
4.2.3.4. Sequence Diagram of LegalEase
 
Figure 4.6 Sequence Diagram of LegalEase
4.2.3.5. Component Diagram of LegalEase
 
Figure 4.7 Component Diagram of LegalEase
4.3. Chapter Summary
This chapter detailed the architectural and logical design of LegalEase, establishing the blueprint for its development and implementation. The Incremental Software Development Model was selected as the guiding process, allowing for the modular construction of features such as document analysis, summarization, and expert referrals. This approach was chosen to mitigate risks and enable continuous user feedback throughout the development lifecycle, despite potential challenges regarding module integration and dependency management. The chapter further defined the system methodology, visualizing the complete flow from requirement analysis to deployment. To structure the system’s data, an Entity Relationship Diagram (ERD) was designed, mapping the relationships between users, legal documents, templates, and expert resources. Finally, a comprehensive set of Unified Modeling Language (UML) diagrams was presented to specify the system's structure and behavior. The Use Case Diagram outlined user interactions with core modules, while the Class Diagram defined the object-oriented structure and backend logic. The dynamic behavior of the system was illustrated through Activity and Sequence Diagrams, which detailed the logic flow for text, voice, and document inputs. The Component Diagram concluded the design phase by visualizing the high-level organization of the web portal, NLP engine, and database infrastructure. Collectively, these design artifacts provide a robust foundation for the subsequent implementation phase of LegalEase.

 
REFERENCES

[1] 	J. Devlin, M.-W. Chang, K. Lee and K. Toutanova, “BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding,” in Proceedings of the NAACL, Minneapolis, MN, 2019. 
[2] 	R. Susskind, Tomorrow’s Lawyers: An Introduction to Your Future, Oxford: Oxford University Press, 2013. 
[3] 	Pakistan, Law and Justice Commission of, “Judicial Statistics of Pakistan 2024,” Law & Justice Commission of Pakistan, Islamabad, 2024.
[4] 	K. Khan, W. Khan and A. Khan, “Urdu Sentiment Analysis Using Supervised Machine Learning Approach,” International Journal of Pattern Recognition and Artificial Intelligence, vol. 32, no. 01, 2021. 


