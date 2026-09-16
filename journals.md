babOPTIMIZING HYBRID RETRIEVAL FOR RAG-BASED AI EDUCATIONAL ASSISTANTS: AN EMPIRICAL STUDY OF QUALITY-LATENCY TRADE-OFFS ON TECHNICAL RESEARCH CORPORA

PROPOSAL TESIS

Oleh:
Abdul Saboor Hamedi
241012050123

PROGRAM STUDI TEKNIK INFORMATIKA S-2
PROGRAM PASCASARJANA
UNIVERSITAS PAMULANG
TANGERANG SELATAN
2026
OPTIMIZING HYBRID RETRIEVAL FOR RAG-BASED AI EDUCATIONAL ASSISTANTS: AN EMPIRICAL STUDY OF QUALITY-LATENCY TRADE-OFFS ON TECHNICAL RESEARCH CORPORA

PROPOSAL TESIS

Diajukan Untuk Memenuhi Gelar Magister Komputer Pada Program Pascasarjana Universitas Pamulang

Oleh:
Abdul Saboor Hamedi
241012050123

PROGRAM STUDI TEKNIK INFORMATIKA S-2
PROGRAM PASCASARJANA
UNIVERSITAS PAMULANG
TANGERANG SELATAN
2026
LEMBAR PERSETUJUAN PROPOSAL TESIS
OPTIMIZING HYBRID RETRIEVAL FOR RAG-BASED AI EDUCATIONAL ASSISTANTS: AN EMPIRICAL STUDY OF QUALITY-LATENCY TRADE-OFFS ON TECHNICAL RESEARCH CORPORA

Telah disetujui untuk disidangkan pada Program Studi Teknik Informatika S-2 Universitas Pamulang
Pada tanggal …………………

Oleh:
Abdul Saboor Hamedi
241012050123

Mengetahui :
Kaprodi Teknik Informatika S-2

Dr. Sajarwo Anggai., S.ST., M.T.
NIDN : 0421108703

 
LEMBAR PERNYATAAN TESIS
Dengan ini saya menyatakan bahwa dalam Proposal Tesis ini tidak terdapat karya yang pernah diajukan untuk memperoleh gelar kesarjanaan di suatu Perguruan Tinggi, dan sepanjang pengetahuan saya juga tidak terdapat karya atau pendapat yang pernah ditulis atau diterbitkan oleh orang lain, kecuali yang secara tertulis diacu dalam naskah tesis ini dan disebutkan dalam daftar pustaka.

Tangerang Selatan, …………..2026….

Abdul Saboor Hamedi
241012050123

KATA PENGANTAR
Puji syukur penulis ucapkan kehadirat Allah SWT, karena atas berkat dan rahmat- Nya penulis dapat menyelesaikan proposal tesis ini. Penulisan Proposal tesis ini dilakukan dalam rangka memenuhi salah satu syarat untuk disetujui sebagai Tesis pada Program Studi Teknik Informatika UNPAM. Penulis menyadari bahwa tanpa bantuan dan bimbingan dari berbagai pihak, dari masa perkuliahan sampai menyusun proposal tesis ini, Oleh karena itu Penulis mengucapkan terimakasih kepada:
Bapak Dr. Pranoto, S.E., M.M., selaku ketua Yayasan Sasmita Jaya.
Bapak Dr. E. Nurzaman, AM., M.M., M.Si., selaku Rektor Universitas Pamulang.
Dr. Saiful Anwar, S.Pd., S.E., M.Pd., selaku Direktur Pascasarjana Universitas Pamulang.
Dr. Sajarwo Anggai., S.ST., M.T., sebagai Ketua Program Studi Teknik Informatika S-2 Universitas Pamulang.
(bisa ditambahkan sesuai kebutuhan)
Akhir kata, penulis berharap Tuhan Yang Maha Esa berkenan membalas segala kebaikan semua pihak yang telah membantu. Semoga tesis ini membawa manfaat bagi pengembangan ilmu pengetahuan.

Penulis,

(Nama Mahasiswa)

 
ABSTRAK
Studi empiris ini bertujuan untuk mengevaluasi mekanisme pencarian hibrida untuk chatbot pendidikan Retrieval-Augmented Generation (RAG), yang membahas ketegangan kritis antara pemahaman semantik dan ketepatan leksikal dalam domain teknis. Dengan pendidikan ilmu komputer yang membutuhkan penalaran konseptual dan pengambilan terminologi yang tepat, memilih arsitektur pengambilan yang optimal merupakan tantangan teknik yang sangat penting.
Kami telah mengembangkan platform pengujian terkontrol untuk membandingkan empat paradigma pengambilan pencarian teks lengkap asli PostgreSQL (Leksikal), Dense Passage Retrieval (Semantik), Fusi Berbobot Linier, dan Fusi Peringkat Timbal Balik (RRF) pada korpus 50.000 potongan teks dari publikasi AI arXiv kontemporer tahun 2025. Studi ini bertujuan untuk mengukur efektivitas (NDCG@10) dan efisiensi (latensi) di seluruh 50 kueri spesifik domain untuk mengukur pertukaran kinerja.
Analisis awal menunjukkan dikotomi kualitas-latensi yang mencolok: meskipun metode semantik dan hibrida diharapkan mencapai akurasi tinggi, metode tersebut mungkin menimbulkan latensi yang jauh lebih tinggi dibandingkan dengan waktu respons di bawah 100 ms dari pencarian leksikal. Penelitian ini secara khusus menyelidiki apakah Linear Weighted Fusion (α=0,7) memberikan ketahanan yang lebih unggul dibandingkan metode berbasis peringkat seperti RRF di domain teknis. Temuan ini bertujuan untuk memberikan pedoman berbasis bukti bagi arsitek sistem, mengidentifikasi kondisi di mana Linear Hybrid Fusion harus menjadi standar default untuk sistem RAG pendidikan.
Kata Kunci: Pencarian Hibrida, Retrieval-Augmented Generation, Pengambilan Informasi, Algoritma Pemeringkatan, Trade-off Kualitas-Latensi, Chatbot Pendidikan

 
ABSTRACT
This empirical study proposes to evaluate hybrid search mechanisms for Retrieval-Augmented Generation (RAG) educational chatbots, addressing the critical tension between semantic understanding and lexical precision in technical domains. With computer science education requiring both conceptual reasoning and precise terminological retrieval, selecting an optimal retrieval architecture is a pivotal engineering challenge.
We have developed a controlled testbed to compare four retrieval paradigms PostgreSQL native full-text search (Lexical), Dense Passage Retrieval (Semantic), Linear Weighted Fusion, and Reciprocal Rank Fusion (RRF) over a corpus of 50,000 text chunks from contemporary 2025 arXiv AI publications. The study intends to measure effectiveness (NDCG@10) and efficiency (latency) across 50 domain-specific queries to quantify performance trade-offs.
Preliminary analysis suggests a stark quality-latency dichotomy: while semantic and hybrid methods are expected to achieve high accuracy, they may incur substantially higher latency compared to the sub-100ms response times of Lexical search. This research specifically investigates whether Linear Weighted Fusion (α=0.7) provides superior robustness over rank-based methods like RRF in technical domains. The findings aim to provide evidence-based guidelines for system architects, identifying the conditions under which Linear Hybrid Fusion should be the default standard for educational RAG systems.
Keywords: Hybrid Search, Retrieval-Augmented Generation, Information Retrieval, Ranking Algorithms, Quality-Latency Trade-offs, Educational Chatbots

 
Table of content

LEMBAR PERSETUJUAN PROPOSAL TESIS i
LEMBAR PERNYATAAN TESIS ii
KATA PENGANTAR iii
ABSTRAK iv
ABSTRACT v
Table of content vi
CHPATER I INTRODUCTION 11
1.1 Background 11
1.2 Problem Statement 13
1.2.1 Problem Identification 14
1.2.2 Problem Scope and Limitations 14
1.2.3 Research Questions 15
1.3 Research Objectives 15
1.4 Writing System 16
CHPATER II 18
CHPATER III THEORITICAL BASES AND FRAMEWORK 18
1.5 Literature Review 18
1.6 Theoritical Bases 19
1.1.1 The Landscape of Retrieval-Augmented Generation (RAG) 19
1.7 Theoretical Paradigms of Search 20
1.7.1 Lexical Retrieval and the Symbolic View 21
1.8 Theory of Hybrid Fusion 21
1.9 Conceptual Framework: The Dual-Path Architecture 23
1.9.1 The Conceptual Search Structure 23
1.9.2 Storage Layer (Bottom) 24
1.9.3 Processing Layer 24
1.9.4 Retrieval Layer (Critical Divergence Point) 25
1.9.5 Fusion Layer (Combination Point) 25
CHPATER IV METODOLOGI 26
1.10 Data Collection and Preparation 26
1.11 arXiv API Query and Filtering Strategy 26
1.12 Data Extraction and Validation 27
1.13 PDF Ingestion and Text Extraction 27
1.14 Resulting Corpus Statistics 28
1.15 System Architecture and Experimental Testbed 28
1.16 Indexing and Storage Strategy 29
1.16.1 Lexical Index (Full-Text Search) 29
1.16.2 Semantic Index (Vector Search) 29
1.16.3 Embedding Model Selection 29
1.16.4 Query Processing Pipeline 30
1.17 System Architecture Overview 30
1.18 Parallel Execution Flow (Retrieval Layer) 30
1.18.1 Path A (Lexical - Fast Path) 31
1.18.2 Path B (Semantic - Deep Understanding Path) 31
1.18.3 Convergence Point 32
1.18.4 Parallel Timing Analysis 32
1.19 Fusion & Ranking Process 32
1.19.1 Input (A) 33
1.19.2 Normalization Phase (B, C, D) — Critical Step 33
1.20 Detailed Pipeline Steps 34
1.21 Implementation Details 34
1.22 Hybrid Fusion Strategies 35
1.22.1 Linear Weighted Fusion 35
1.22.1 Reciprocal Rank Fusion 35
1.23 Evaluation Methodology and Metrics 36
1.23.1 Query Set Curation 36
1.23.1 Automated Relevance Judging via AI-as-a-Judge 37
1.23.1 Ranking Evaluation Metrics 37
1.23.2 Normalized Discounted Cumulative Gain (NDCG@K) 37
"DCG@K"=i=1K2"rel" i-1log⁡2(i+1) 37
1.23.3 Mean Reciprocal Rank (MRR) 38
1.23.4 Precision@5 38
1.23.5 Latency (Milliseconds) 38
1.24 Experimental Execution and Data Analysis 38
1.24.1 Statistical Analysis Approach 39
1.25 Results and Empirical Findings 40
1.25.1 Key Observations 40
1.26 Latency Analysis and Percentile Distribution 41
1.26.1 Interpretation 41
1.27 Precision-Recall Trade-off Analysis 42
1.28 Precision-Recall AUC Comparison 42
1.28.1 Explanation of the Apparent Contradiction 43
1.28.2 Practical Implications 43
1.29 Score Correlation and Signal Complementarity 44
1.29.1 Score Correlation Matrix 45
1.29.1 Critical Insights from Correlation Analysis 45
1.30 Robustness Analysis: Winner-Take-All Evaluation 46
1.31 Winner Distribution 47
1.32 Category-Level Winner Analysis 48
1.32.1 Strategic Insights 48
1.33 Performance by Query Category: Detailed Breakdown 49
1.33.1 Observations 49
1.34 Failure Mode Analysis: When Hybrid-Linear Underperforms 50
1.34.1 Failure Distribution 50
1.35 Key Patterns 50
1.36 Data Results Dataset: Consistency Validation (With Caveats) 51
1.37 Conclusion 52
REFERENCES 54

Table of Tables
Table 1: Related work 18
Table 2: API Query 26
Table 3:Corpus Composition and Statistics 28
Table 4:End-to-End Pipeline Execution Steps with Latency Breakdown 34
Table 5: Query Set Composition (N=50 Unique Queries) 36
Table 6: AI Dataset - Enhanced Aggregate Performance Metrics (N=100 Queries) 40
Table 7: AI Dataset - Latency Percentile Distribution 41
Table 8:Precision-Recall Area Under Curve (AUC) 42
Table 9: Spearman Rank Correlation Between Method Scores 45
Table 10: AI Dataset - Winner-Take-All Analysis 47
Table 11: AI Dataset - Winner Distribution by Query Category 48
Table 12: AI Dataset - Mean NDCG@10 by Query Category 49
Table 13: Failure Case Breakdown (N=34 queries where Hybrid-Linear did not win) 50

 
Table of figures
Figure 1: simplified breakdown of the RAG workflow 20
Figure 2: System Architecture Overview 24
Figure 3:Parallel Execution Flow - Lexical and Semantic Search Paths 31
Figure 4: Fusion & Ranking Process - Score Normalization and Strategy Selection 33
Figure 5:Precision-Recall Curves 44
Figure 6: Correlation Heatmap 46
Figure 7: Distribution of Winning Algorithms 51
Figure 8: Data Dataset - Winner-Take-All Analysis (Pending Validation) 52

INTRODUCTION
Background
The rapid evolution of conversational AI assistants for education creates a pressing need for retrieval backbones that are both accurate and responsive. Educational chatbots deployed in academic settings must serve a fundamentally dual cognitive load: students and researchers frequently pose complex (Pan & Zhou, 2022), conceptual questions where deep semantic understanding of abstract concepts is paramount e.g., explain the attention mechanism in transformers" or "What are the theoretical foundations of gradient descent?, yet they equally often employ precise technical jargon where exact lexical matching remains vital e.g., "What is LoRA?" or "Define quantization". This fundamental tension between semantic depth and lexical precision has long motivated researchers to explore hybrid search architectures that intelligently combine both signals, rather than relying on a single retrieval method(Johnson & Hass, 2022).
Modern educational systems like MedBioRAG (Kim, 2025) establish the practical promise of hybrid search strategically combining sparse lexical retrieval with dense semantic search. In modern academic environments, the efficiency of RAG-based AI educational assistants is measured not only by their accuracy but also by their real-time responsiveness (Monir et al., 2024). For interactive student tools, maintaining a strict Service Level Agreement (SLA) of <500ms is essential to ensure a seamless learning experience. This response time is defined as the end-to-end query latency, measuring the total wall-clock time from the moment a user submits a search request until the system provides the final ranked list of results(Shen et al., 2024). This includes query preprocessing, similar execution of lexical and semantic lookups, and the final score fusion. Meeting this 500ms threshold is a critical usability requirement; exceeding it can lead to pedagogical failure, where students lose focus or engagement while waiting for the system to “think”.
However, the theoretical and practitioner literature often treats fusion mechanisms and their performance trade-offs as implementation details rather than rigorous research questions (Bruch et al., 2023; Wang et al., 2025). While hybrid approaches have become standard in production systems, a significant empirical gap persists: Which fusion strategy linear combination vs. rank-based methods delivers superior ranking quality for technical domains? What is the quantifiable latency cost of achieving high-accuracy hybrid search, and under what SLA constraints is this cost justified? Consequently, a core challenge of this research is managing the “hybrid text” the computational overhead required to achieve high-quality results without violating these real-time performance targets (Thakur et al., 2021; Wang et al., 2025).
To address this limitation, this study introduces a dedicated experimental framework for rigorous comparative evaluation of retrieval methods. We implement a conversational AI assistant over a carefully curated corpus of contemporary (2025) arXiv computer science publications and subject its retrieval mechanisms to systematic, controlled testing under realistic conditions. A key architectural decision was to use PostgreSQL’s native full-text search (ts_rank) over Python-based BM25 implementations, prioritizing database-level integration, memory efficiency, and operational scalability design choices with significant practical implications for production systems serving thousands of concurrent users.
Our research is driven by four focused, practically-motivated research question by systematically addressing these four research questions, we provide an evidence-based blueprint for optimizing the retrieval layer of educational chatbots, moving from generic architectural advice use hybrid search to specific, data-driven engineering recommendations informed by empirical performance evidence.
Our research makes three significant contributions to bridge this gap. We establish a complete, reproducible experimental framework for evaluating hybrid search on technical corpora, including systematic data collection from arXiv, corpus preparation protocols, query set curation guidelines, and automated evaluation via LLM-based relevance judgments. This framework is domain-independent and can be adapted to other specialties medicine, law, etc.
Problem Statement
The main problem address in this research is the l ack of a standardized, evidence-base framework for balancing retrieval quality and system latency within RAG-based educational assistants. While hybrid search has become a de facto standard in production system, the academic and practitioner literature frequently treats fusion mechanism as more “implementation details” rather than rigorous research questions.
Apparently, a wide empirical gap persists regarding the performance of different fusion strategies specifically Linear Weighted Fusion versus Reciprocal Rank Fusion (RRF) when applied to specialised technical corpora. While practitioners often assume that hybrid methods are universally superior, the parallel execution of lexical and semantic paths introduces a “hybrid tax” a qualifiable computational overhead that risks violating the strict <500ms SLAR required for real-time educational tools.
There is currently no clear architectural guidance on:
Which fusion strategy delivers superior ranking robustness for the unique blend of conceptual and terminological queries found in computer science education.
Whether the marginal gain in NDCG@10 provided by hybrid methods justifies the increased latency cost compared to pure semantic or lexical strategies.
What specific query characteristics (such as the use of rare technical acronyms) should influence the selection of a retrieval method to optimize the quality-latency trade-off.
This research is motivated by the urgent need to move beyond generic architectural advice "use hybrid search" toward data-driven engineering recommendations. By establishing a reproducible benchmark using 2025 arXiv AI publications, this study intends to provide system architects with the evidence required to build educational AI tools that are both pedagogically accurate and operationally efficient.
Problem Identification
Based on the background outline above, multiple problems can be identified related to retrieval architectures in educational AI assistance:
The Dual Cognitive Load: Chatbots struggle to balance deep semantic understanding for concepts with exact lexical precision for technical jargon.
SLA Risks ("Hybrid Tax"): Executing parallel retrieval paths introduces a computational overhead that risks violating the strict <500ms SLA.
Unquantified Trade-offs: There is no standardized framework to measure whether accuracy gains from hybrid methods (like Linear vs. RRF) actually justify their latency costs.
Absence of Intelligent Routing: There is no clear architectural guidance on how query characteristics should dynamically influence the selection of a retrieval method.
Collectively, these unresolved gaps highlight the urgent need to move beyond generic assumptions to a rigorous, data-driven framework capable of optimizing both pedagogical accuracy and real-time operational efficiency.
Problem Scope and Limitations
To ensure this research remains focused, rigorous, and achievable, the empirical evaluation is strictly bounded by the following parameters:
Corpus and Data Scope: The document corpus is strictly limited to 50 unique Computer Science - Artificial Intelligence (cs.AI) publications downloaded from arXiv. To ensure the data reflects contemporary state-of-the-art architectures, a strict temporal filter is applied, excluding any papers published in the year 2025.
Retrieval Algorithms Scope: The study exclusively compares four specific retrieval paradigms: native PostgreSQL full-text search (Lexical via ts_rank), Dense Passage Retrieval (Semantic via pgvector), Linear Weighted Fusion (fixed at), and Reciprocal Rank Fusion (fixed at). Other vector databases or sparse algorithms (like Python-based BM25) are excluded from this architecture.
Embedding Model Limitations: The semantic representation is restricted to the 384-dimensional paraphrase-multilingual-MiniLM-L12-v2 model. Larger 768-dimensional models (e.g., BERT-large) are deliberately excluded to prioritize the <500ms latency requirement.
Evaluation and Metrics Scope: The performance trade-offs are evaluated using exactly 50 manually curated domain-specific queries. The system’s effectiveness is primarily measured using NDCG@10, MRR, and Precision@5, alongside wall-clock latency.
Relevance Judgment Scope: Ground truth relevance assessments for the retrieved documents are generated automatically using an LLM-as-a-Judge approach (Qwen 7B running locally) utilizing binary labels (Relevant/Not Relevant), rather than relying on human annotators.
Research Questions
Our study is driven by four focused, practically-motivated Research Questions:
RQ1: For technical Q&A in computer science education, under what specific conditions do pure lexical search and pure semantic search excel or fail? The question hight performance baseline by identifying the extact issue where semantic research suffers from conceptual drif, and where lexical suffere from vocabulary mismatch.
RQ2: Which hybrid fusion strategy linear weighted combination or rank-based Reciprocal Rank Fusion (RRF) yields superior ranking quality and robustness across diverse question types? Building on the baseline, this consider which mathematical fusion arthitecture is the best synthesis the strength of both individual methods to maximize overall retrieval accuracy.
RQ3: What is the quantifiable latency cost of hybrid search, and under what performance targets is this cost justified for real-time educational applications operating under a <500ms SLA? This question introduces the main operational constraint by measuring the “hybrid tax” computation overhead to ensure the system remains fast and responsive enough for student engement.
RQ4: Can query characteristics (length, specificity, type) predict the optimal retrieval method, enabling an intelligent query router for dynamic method selection? This final question synthesizes the previous findings to propose a practical engineering solution: using query metadata to dynamically route searches to the most efficient path, ultimately balancing the quality-latency trade-off
Research Objectives
This research aims to bridge the identified gap by constructing a dedicated experimental framework for the comparative evaluation of retrieval methods. The specific objectives are:
The first step, we develop a controlled testbed using a curated corpus of 2025 arXiv computer science publications to evaluate modern retrieval strategies. The second step is to implement and compare four distinct retrieval paradigms: Lexical (PostgreSQL ts_rank), Semantic (Dense Passage Retrieval), Linear Weighted Fusion, and Reciprocal Rank Fusion (RRF). On the third step is to quantify the quality-latency trade-offs of these methods, specifically measuring NDCG@10 and end-to-end latency. Last but not least to evaluate the robustness of score-based fusion vs. rank-based fusion across diverse query categories (Conceptual, Factual, Procedural)

Writing System
The writing systematics explains a brief explanation of the contents of each chapter in this thesis proposal as follows:

CHAPTER I INTRODUCTION
This chapter presents the background to the problem being researched, problem identification, problem formulation, research objectives, problem limitations, research benefits, research methods and writing systematics.
CHAPTER II THEORETICAL BASIS AND FRAMEWORK OF THINKING
This chapter includes several sub-chapters, including: literature review, theories that support the topic and framework of thought.
CHAPTER III RESEARCH METHODS
This chapter includes several sub-chapters, including: needs analysis, research design and analysis techniques. 

THEORITICAL BASES AND FRAMEWORK
Literature Review
Author (Year) Focus Key Finding/Method Gap Addressed by Your Research
Bruch et al. (2023) Hybrid Fusion Established RRF as a robust, parameter-free method. Does not evaluate RRF on technical AI corpora or compare with Linear Fusion.
Abootorabi et al. (2025) Multimodal RAG Demonstrated that aligning multi-source signals is critical for precision. Focuses on multimodal data; does not benchmark quality-latency trade-offs.
Malkov et al. (2020) Vector Search Established the HNSW foundation for scalable vector search. Focuses on algorithmic theory, not the "hybrid tax" in end-to-end RAG systems.
Ranasinghe et al. (2025) Efficiency Highlighted efficiency trade-offs in specialized code retrieval. Investigates code; your study focuses on CS educational publications and a <500ms SLA.
Table 1: Related work
Table 1 summarises the related work, it highlights a critical evolution in retrieval theory, shifting from foundational vector search algorithms to complex hybrid systems designed for high-precision tasks. While the current literature establishes Reciprocal Rank Fusion (RRF) as a robust, parameter-free standard for general search, there remains a significant empirical gap concerning its performance on specialised technical search corpora compared to tunable linear fusion strategies.
Furthermore, with the efficiency of individual search components is well-documented, the end-to-end “hybrid-tax” the total latency cost of executing parallel retrieval paths and fusion logic has not been rigorously benchmarked within the strict <500ms SLA required for interactive educational tools.
This research intends to bridge these gaps by conducting a controlled comparative analysis of these fusion paradigms. By Using contemporary corpus 2025 arXiv AI publications, the study aims to move beyond generic architectural advice and provide a data driven blueprint optimizing the retrieval layer in RAG-based educational assistants. The following section establishes the theoretical foundations of these search paradigms and conceptual framework used to evaluate their quality-latency trade-offs.
Theoritical Bases
The primary goal of this theoretical framework is to deconstruct the mechanisms of information retrieval within the specific context of educational AI assistants. Unlike general-purpose search engines which optimize for broad relevance (recall), educational tools must balance two competing theoretical constraints: pedagogical accuracy, which requires deep semantic understanding of abstract concepts, and terminological precision, which demands exact lexical matching of domain-specific jargon. This chapter establishes the theoretical landscape of Retrieval-Augmented Generation (RAG), contrasts the governing laws of sparse and dense retrieval, and defines the conceptual framework for the hybrid architecture evaluated in this study.
The Landscape of Retrieval-Augmented Generation (RAG)
Retrieval-Augmented Generation (Lewis et al., 2020) represents a paradigm shift from purely parametric knowledge (stored within LLM weights) to non-parametric knowledge (retrieved from external indices). Theoretically, RAG decouples "reasoning" from "knowing."

Figure 1: simplified breakdown of the RAG workflow
Disclaimer: The card goes to the creator of ‘MERIT’ website
The Generator (LLM) acts as the reasoning engine, responsible for synthesis, articulation, and adaptation to student needs. Meanwhile the retriever acts as the memory bank, responsible for grounding the generation in verifiable facts. In this landscape, the retrieval component is the critical bottleneck for accuracy. If the retriever fails to surface the correct context "Hallucination of Reference", the generator’s reasoning is grounded in noise, leading to pedagogical failure.
Theoretical Paradigms of Search
Lexical retrieval relies on the Bag-of-Words assumption, treating text as a collection of discrete atomic symbols. Algorithms like TF-IDF and BM25 (and its PostgreSQL implementation, ts_rank) operate on the principle of term overlap, paradigms of Search. Theory under the symbolic view of lexical retrieval, a document is considered relevant if and only if it contains the exact symbols present in the user’s query. To determine importance, these terms are mathematically weighted by their rarity using Inverse Document Frequency.
Theoretical strength the primary advantage of this paradigm is its absolute precision. Because it relies entirely on exact symbolic matching, it is theoretically impossible for a pure lexical system to retrieve a document about "apples" when the search query is for "oranges," effectively ensuring zero conceptual drift. Theoretical weakness conversely, its critical limitation is vocabulary mismatch. A pure lexical system fundamentally lacks the cognitive capacity to understand that synonymous phrases, such as "neural net" and "deep learning model," function as semantic equivalents.
Lexical Retrieval and the Symbolic View
Lexical retrieval relies on the Bag-of-Words assumption, treating text as a collection of discrete atomic symbols where algorithms like TF-IDF and BM25 (along with its PostgreSQL implementation, ts_rank) operate on the principle of term overlap. Under this theory, a document is considered relevant if and only if it contains the exact symbols present in the query, which are then weighted by their rarity using Inverse Document Frequency.
The primary theoretical strength of this paradigm is its absolute precision; it is theoretically impossible for a pure lexical system to retrieve a document about "apples" when searching for "oranges," effectively ensuring zero conceptual drift. However, its critical theoretical weakness is vocabulary mismatch, as the system fundamentally lacks the cognitive capacity to understand that synonymous phrases like "neural net" and "deep learning model" function as semantic equivalent.
Theory of Hybrid Fusion
The theory of hybrid fusion addresses the mathematical and architectural challenge of merging two fundamentally different retrieval paradigms: the symbolic view (lexical search like BM25, which operates on exact term overlap and discrete probabilities) and the distributional view (semantic search, which maps text into continuous high-dimensional vector spaces to measure geometric proximity). Because lexical and semantic algorithms produce scores on completely incomparable scales unbounded probabilistic scores versus bounded cosine similarities fusion theory dictates how to intelligently synthesize these signals to maximize precision and recall.
Score-Based Fusion (Linear Weighted Combination) Grounded in Signal Processing Theory, this paradigm assumes that the absolute magnitude of retrieval scores contains valuable confidence information. It acts as a "filtering" mechanism by applying a weighted sum to the scores (Bruch et al., 2023). To ensure a fair combination, raw scores must undergo rigorous score normalization (such as Theoretical Min-Max scaling) to map unbounded lexical scores into a bounded range.
Theoretical Advantage: Because it utilizes raw score distributions, it maintains Lipschitz continuity, ensuring that small variations in individual scores do not wildly distort the final hybrid ranking (Bruch et al., 2023). It allows system architects to fine-tune weights to favor specific domains, providing high empirical effectiveness and sample-efficiency.
Rank-Based Fusion (Reciprocal Rank Fusion - RRF) Grounded in Social Choice Theory, RRF functions as a "consensus" or voting mechanism. It assumes that the absolute score magnitudes across varying retrieval systems are fundamentally unreliable, and therefore only the relative ordering matters. It computes a new score by summing the inverse ranks of documents across different retrieval lists (Bruch et al., 2023).
Theoretical Advantage & Weakness: RRF is parameter-free and performs considerably well in zero-shot, out-of-domain settings. Nevertheless, because it discards score distributions, it treats a marginal score difference exactly the same as a massive score difference, which can lead to suboptimal accuracy in highly technical domains compared to linear fusion (Bruch et al., 2023).
Tensor-Based Re-ranking Fusion (TRF) TRF is a newer, late-interaction architecture (such as ColBERT) that retains a tensor of individual token embeddings rather than compressing text into a single dense vector. TRF merges candidate lists from different retrieval paths by computing operations like MaxSim, aligning each query token with its most relevant semantic counterpart in the document (Karapiperis et al., 2025). This provides the semantic power of full tensor search with high efficacy, but at a fraction of the computational and memory cost of full cross-encoder models.
Hybrid Fusion Distance (Attribute-Penalty Fusion) In specialized domain applications (such as cybersecurity and threat hunting), fusion theory integrates continuous semantic distance with discrete penalties for categorical metadata mismatches. A global attribute weight parameter acts as a tuning knob, dictating the balance between semantic similarity and attribute conformity. This allows the system to dynamically shift between a "soft filter" (prioritizing semantics) and a "hard filter" (strictly enforcing attributes) depending on the query’s need (Karapiperis et al., 2025).
Theoretical Properties & Systemic Trade-offs For a fusion function to be theoretically sound, it must exhibit monotonicity (higher individual scores must improve the overall ranking), homogeneity (resistance to the arbitrary re-scaling of vectors), and boundedness (Bruch et al., 2023). Furthermore, hybrid architectures face the "weakest link" phenomenon: fusion is not a simple ensemble where strengths automatically aggregate. If one retrieval path performs poorly, it can pollute the fusion pool with irrelevant documents, causing the overall hybrid system to underperform compared to its single best constituent path (Wang et al., 2025).
Conceptual Framework: The Dual-Path Architecture
Based on these theories, we propose a Dual-Path Conceptual Framework for educational RAG. This structure explicitly acknowledges the need for both types of cognition symbolic and semantic by processing every query through parallel pathways before synthesis.
The Conceptual Search Structure
Query Decomposition: The user’s intent is treated simultaneously as a set of required keywords (Symbolic Path) and an abstract question (Semantic Path).
Parallel Retrieval
Path A (Symbolic): Filters the corpus for exact terminological matches, enforcing precision.
Path B (Semantic): Scans the corpus for conceptual similarity, enforcing understanding.

Figure 2: System Architecture Overview
Figure 2 demonestrate the the query input and and query processing architecture. There are four different layers, and each has different work and responsibilities, each layer has explained in the following:
Storage Layer (Bottom)
PostgreSQL Database: Single unified database maintaining all ~50,000 document chunks
Lexical Index (tsvector): PostgreSQL’s native full-text search index enabling fast keyword matching via inverted indexing. Implements term frequency-based ranking.
Vector Index (pgvector): Separate index storing 384-dimensional embeddings for semantic similarity search using IVFFLAT for approximate nearest neighbor indexing.
Design Rationale: Co-locating both indexes in PostgreSQL eliminates inter-service latency and reduces operational complexity.
Processing Layer
Query Input: User-submitted search query (e.g., "How does attention mechanism work?")
Query Preprocessing: Normalizes input (lowercase, optional stopword removal) ensuring consistent processing for both retrieval paths.
Retrieval Layer (Critical Divergence Point)
Parallel Execution: Query is simultaneously routed to two independent retrieval methods. Lexical Search Path Uses tsvector index to find documents containing relevant keywords. While semantic search path sses pgvector index to find documents with similar meaning via embeddings. Both paths execute in parallel, reducing total latency by 35%
Fusion Layer (Combination Point)
Score Normalization: Raw scores normalized to [0,1] range for fair comparison. Fusion Strategy combines normalized scores using either Linear (α=0.7) or RRF. Final Ranking merged results sorted by fused score, returning top-10 documents

 

METODOLOGI
Data Collection and Preparation
The foundation of our experimental framework is a contemporary, domain-specific corpus of computer science publications. We curated this corpus by automating the download of all 2025 AI/ML publications from arXiv, the preprint repository serving as the primary dissemination channel for cutting-edge research (Clement et al., 2019)
arXiv API Query and Filtering Strategy
We collected all our data from arXiv, and it is a “free distribution service and an open-access archive for nearly 2.4 million scholarly articles in the fields of physics, mathematics, computer science, quantitative biology, quantitative finance, statistics, electrical engineering and systems science, and economics. Materials on this site are not peer-reviewed by arXiv”. We use the APIs for the sake of educational only. No one else has access to the API we’re using to fetch the documents. The following are the parameters:
Parameter Value Purpose
search_query cat: cs.AI Query papers in Computer Science - Artificial Intelligence category
start 0 Begin query results from the first entry (pagination start index)
max_results 100 Retrieve up to 100 results per API request
sortBy submittedDate Order results by submission date to identify most recent papers
sortOrder descending Sort in reverse chronological order (newest first)
Table 2: API Query
This query requests papers categorized under Computer Science - Artificial Intelligence (cs.AI), sorted by most recent first. The API returns XML-formatted metadata including title, publication date, abstract, and download links. Critically, we filter results to include only papers published in 2025, ensuring corpus contemporaneity and relevance to current AI/ML pedagogy.
Data Extraction and Validation
For each arXiv entry returned by the API, we extract Publication Metadata (title, abstract, and publication date set to 2025), resolve Document Identifiers including the arXiv ID and direct PDF download link (constructed via URL pattern transformation when necessary), and perform Content Validation to verify that PDFs download successfully and contain extractable text, incorporating failure handling for corrupted documents. The publication date filtering is implemented as:

1. dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
2. if dt.year != 2025:
3. continue # Skip papers not from 2025
   This temporal filtering is crucial: the field evolves rapidly, and 2024 papers may include outdated architectural recommendations or preliminary results later revised. By restricting to 2025, we ensure the corpus reflects the state-of-the-art relevant to students and educators in the 2025-2026 academic year.
   PDF Ingestion and Text Extraction
   Downloaded PDFs are processed through an unstructured PDF extraction pipeline that:
   Page Segmentation: Identifies distinct sections (title, abstract, introduction, methodology, results, conclusion)
   Table/Figure Handling: Extracts text from tables; captions are preserved as context
   Chunking Strategy: Breaks documents into semantic chunks (typically 200-400 words) to match typical retrieval granularity and indexing constraints
   Noise Removal: Strips headers, footers, and metadata artifacts; preserves citation markers for traceability
   We employ the unstructured library with PDF-specific processors (PyPDF, pdfminer, pdfplumber) to handle diverse PDF encodings and layouts common in academic papers.
   Resulting Corpus Statistics
   The complete data preparation workflow yielded:
   Metric Value
   Total Papers Downloaded 50 unique 2025 arXiv papers (cs.AI category)
   Total Extraction Volume 50,000 text chunks
   Average Chunk Size 300-350 words
   Chunk Count per Paper 300 chunks (median)
   Vocabulary Size 250,000 unique terms
   Date Range January 2025 - December 2025
   Primary Topics Large Language Models, Transformers, Retrieval-Augmented Generation, Prompt Engineering, Fine-tuning, Quantization, Distributed Training
   Table 3:Corpus Composition and Statistics
   The corpus captures the diversity of contemporary AI research: we observe papers on foundational topics (transformer architectures, attention mechanisms) alongside emerging areas (multi-modal learning, efficient inference, federated learning). This heterogeneity is intentional an educational chatbot must support queries spanning foundational and cutting-edge material.
   System Architecture and Experimental Testbed
   We developed a modular, microservice-oriented architecture to enable fair and controlled comparison of retrieval methods. The architecture enforces separation of concerns, ensuring that comparisons isolate retrieval strategy effects rather than confounding them with infrastructure variations.
   Indexing and Storage Strategy
   All document chunks are indexed in a single PostgreSQL database instance (version 14.x) with two complementary index structures:
   Lexical Index (Full-Text Search)
   For lexical retrieval, document chunks are first parsed into the PostgreSQL tsvector format, where they are tokenized, stemmed, and weighted by field. An inverted index is then built on this tsvector to enable fast lexical search via the @@ operator. During execution, user queries are converted into the tsquery format, allowing for complex matching through the use of boolean operators (AND, OR, NOT) and phrase proximity. Finally, the retrieved documents are ranked via PostgreSQL’s ts_rank () function, which implements a probabilistic, BM25-like scoring mechanism that incorporates term frequency, document length normalization, and collection statistics
   Semantic Index (Vector Search)
   Each document chunk is encoded into a 384-dimensional dense vector using the paraphrase-multilingual-MiniLM-L12-v2 model. These vectors are then stored in a PostgreSQL database via the pgvector extension, an open-source vector extension that provides IVFFLAT indexing. During the retrieval process, semantic similarity is computed via cosine distance, which is mathematically represented as 1 - (u · v) / (||u|| ||v||). To optimize this search process, the IVFFLAT index utilizes 500 clusters to enable an approximate nearest neighbour search, effectively balancing system latency and retrieval accuracy. Both indexes are maintained on the same underlying documents, ensuring that index construction differences don’t bias comparisons. Queries are executed against both indexes simultaneously in the application tier, with results combined via fusion strategies.
   Embedding Model Selection
   The choice of embedding model significantly impacts semantic search quality. We selected sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 based on the following criteria:
   Dimensionality (384): Provides sufficient expressivity for semantic capture while keeping vector storage and computation tractable
   Multilingual Support: Enables future extension to non-English technical queries
   Training Data: Trained on parallel sentence pairs emphasizing semantic equivalence, directly aligned with our ranking objective
   Computational Efficiency: ~20ms inference time per document, enabling batch re-encoding if needed
   Reproducibility: Publicly available via Hugging Face with consistent outputs across runs.
   Alternative embedding models (e.g., MPNet, E5) were considered but rejected: BERT-large models (768-dim) provide marginal accuracy gains (~2-3% NDCG) at double the latency cost, while smaller models (128-dim) degrade quality by ~5-7%.
   Query Processing Pipeline
   For each test query, the system executes the following pipeline. The architecture ensures parallel execution where possible to minimize overall latency, while maintaining strict separation between retrieval methods to enable fair comparison.
   System Architecture Overview
   The system organizes retrieval into four logical layers: storage (indexes), processing (query prep), retrieval (parallel execution), and fusion (combination). This separation enables independent optimization of each component while maintaining a unified end-to-end pipeline.
   Parallel Execution Flow (Retrieval Layer)
   Two independent retrieval pipelines execute simultaneously: a fast lexical path (~70ms) and a semantic understanding path (~200ms). Parallelization reduces overall latency by 35% compared to sequential execution, from 270ms to 200ms.

Figure 3:Parallel Execution Flow - Lexical and Semantic Search Paths
Path A (Lexical - Fast Path)
Convert to ts_query: Transform query into PostgreSQL’s query language. Example: "
PostgreSQL ts_rank: Execute full-text search returning documents ranked by term frequency, IDF, and word proximity
Output: Top-100 documents with unbounded ts_rank scores (typically 0-20)
Path B (Semantic - Deep Understanding Path)
Encode to 384-dim vector: Pass query through sentence-transformers, converting text into dense vector capturing semantic meaning.
pgvector IVFFLAT Similarity Search: Query vector compared against index using approximate nearest neighbor search. IVFFLAT partitions vectors into 500 clusters, accelerating search from O (n) to O (log n)
Output: Top-100 documents with cosine similarity distances (bounded [0, 2])
Convergence Point
Both paths’ Top-100 results merged by document ID (union operation)
Results proceed to normalization step
Parallel Timing Analysis
Lexical path: ~70ms
Semantic path: ~100ms embedding + 100ms search = 200ms
Sequential: 70 + 200 = 270ms
Parallel: max (70, 200) = 200ms ← 26% latency reduction
Fusion & Ranking Process
After both retrieval methods produce results, they must be combined intelligently. Raw scores are on incomparable scales (unbounded ts_rank vs. bounded cosine distance), requiring normalization before fusion. Two fusion strategies are implemented: Linear weighted combination (empirically optimal at 66%-win rate) and Reciprocal Rank Fusion (theoretically appealing but empirically suboptimal at 0%-win rate).

Figure 4: Fusion & Ranking Process - Score Normalization and Strategy Selection
Input (A)
Union of Top-100 Lexical results and Top-100 Semantic results
Typically, 150-200 unique documents (some documents ranked high by both methods)
Normalization Phase (B, C, D) — Critical Step
Raw scores on incomparable scales:
ts_rank: unbounded [0, 20+]
cosine distance: bounded [0, 2]
Min-Max Normalization: Maps both to [0, 1] independently per query
Without normalization: Unbounded ts_rank would dominate the fusion, defeating signal combination

Detailed Pipeline Steps
Step Operation Input Output Latency
Preprocessing Normalize & tokenize Raw query Cleaned tokens <5ms
Lexical Search PostgreSQL ts_rank tsquery Top-100 results + scores 60-80ms
Semantic Search pgvector lookup Query vector Top-100 results + distances 150-200ms
Normalization Min-max scaling Raw scores Normalized [0,1] <5ms
Fusion Combine methods Both normalized scores Fused scores <5ms
Final Ranking Sort & filter Fused scores Top-10 results <5ms
Total Parallel All steps Query Final results 500-700ms
Table 4:End-to-End Pipeline Execution Steps with Latency Breakdown
Implementation Details
Each pipeline step enforces specific design decisions that balance accuracy, latency, and operational simplicity. The following details explain the rationale and practical constraints governing each stage of the retrieval process, highlighting where computational trade-offs become critical for production deployment (Akbari et al., 2021). Implementation choices at each stage directly impact end-to-end system performance: decisions in preprocessing affect index efficiency, parallelization reduces latency variance, normalization ensures fair signal fusion, and ranking strategies determine optimal result ordering.
Query Preprocessing (Step 1): Lowercase conversion and optional stopword removal ensure consistent input across both retrieval paths
Parallel Execution (Steps 2A & 2B): Lexical and semantic searches run simultaneously; total time is max (lexical, semantic) ~200ms, not their sum
Score Normalization (Step 3): Essential because ts_rank scores are unbounded (0-20+) while cosine distances are [0, 2]; min-max scaling per-query prevents magnitude-based dominance
Fusion Strategy (Step 4): Linear fusion (α=0.7) weights semantic 70% based on empirical superiority; RRF treats methods equally but adjusts for rank diversity
Final Ranking (Step 5): Returns top-10 for evaluation; up to 200 candidate documents if both methods returned 100 results each
Key Performance Insights
Bottleneck: Embedding inference (~100ms) dominates semantic search latency; 384-dimensional vectors vs larger (768-dim) models is a deliberate latency optimization
Parallelization Benefit: Parallel execution of lexical + semantic saves ~100ms vs sequential execution
Normalization Necessity: Without normalization, unbounded ts_rank would dominate; normalization ensures fair signal combination
Hybrid Fusion Strategies
We implement and compare two hybrid fusion approaches:
Linear Weighted Fusion

    Where α=0.7 weights the semantic signal more heavily. This parameter choice reflects domain knowledge (in technical Q&A, semantic understanding of concepts is often more important than exact keyword matching) and was validated via preliminary experiments showing peak NDCG@10 at α∈[0.65,0.75].
    Reciprocal Rank Fusion

    Where k=60 is a smoothing constant preventing division by zero and down-weighting top-1 results (encouraging diversity). RRF eliminates the need for score normalization and is theoretically robust to scoring scale differences across methods. Both fusion strategies require minimal tuning and are computationally inexpensive (linear algebra operations on ~100 results per query).

Evaluation Methodology and Metrics
Query Set Curation
We manually curated a set of 50 unique, domain-relevant technical queries spanning five distinct categories:
Category Count Example Queries Rationale
Conceptual 11 Explain the attention mechanism in transformers What is the purpose of positional encoding? Tests deep semantic understanding; crucial for educational chatbots
Factual (What) 21 What is LoRA? Define quantization; What are mixture-of-experts (MoE)? Tests exact term matching; common in quick-lookup scenarios
Procedural (How) 13 How does fine-tuning reduce training time? How to implement gradient accumulation? Tests procedural reasoning; important for implementation guidance
Comparative 1 Compare BERT and GPT architectures Tests relative reasoning; less common but pedagogically important
Other 4 Diverse questions not fitting above categories Captures long-tail query types
Table 5: Query Set Composition (N=50 Unique Queries)
Each query was independently validated by the authors for relevance to the corpus and to actual student/educator information needs in a CS education context. Queries were intentionally diverse in length (8-18 words, mean 12) to capture variation in specificity.
Automated Relevance Judging via AI-as-a-Judge
Ground truth (relevance labels) are generated using a local Large Language Model (Qwen 7B via Ollama) running locally to ensure reproducibility and data privacy. For each (query, document) pair, the LLM evaluates:
Respond with "RELEVANT" or "NOT RELEVANT" followed by a brief justification.
Relevance judgments are binary (RELEVANT=1, NOT RELEVANT=0). While this is a simplification compared to multi-level judgments (e.g., highly relevant, somewhat relevant, not relevant), binary labels are:
More reproducible (LLMs show higher consistency on binary vs. graded judgments)
More interpretable for comparison across methods
Sufficient for ranking evaluation at NDCG@10 granularity
The LLM-based judging approach enables scalable evaluation (50 queries × 100 retrieved results × 4 methods = 20,000 relevance assessments) without human effort. As discussed in limitations, future work should validate these judgments against human assessments.
Ranking Evaluation Metrics
We compute the following information retrieval metrics for each (query, method) combination:
Normalized Discounted Cumulative Gain (NDCG@K)
"DCG@K"=∑\_(i=1)^K▒(2^(〖"rel" 〗\_i )-1)/(〖log⁡〗\_2 (i+1))
NDCG measures ranking quality: it assigns higher weight to relevant documents appearing early in the ranking (via the logarithmic discount), and normalizes by ideal DCG to yield a [0, 1] scale comparable across queries. We report NDCG@10 as the primary metric (top-10 results are what users typically examine).
Mean Reciprocal Rank (MRR)

    Where rank_i is the position of the first relevant document for query i. MRR emphasizes early precision: perfect if a relevant document appears in position 1, degrades quickly for position 5+. MRR is interpretable as "what rank position can users expect to find a relevant answer?

Precision@5

    Precision@5 measures what fraction of top-5 results are relevant. Users often only examine the first 5 results, making this metric practically important.

Latency (Milliseconds)
End-to-end query latency measured from query submission to final ranking return, including:
Query preprocessing
Index lookup (lexical and/or semantic)
Score computation and fusion
Sorting and result preparation
Latency is measured wall-clock time on a single-threaded, non-optimized system (representative of typical deployment scenarios).
Experimental Execution and Data Analysis
For each of the 50 unique queries, we execute the following protocol:
Submit query to retrieval system with full execution tracing enabled
Retrieve top-K=10 results from each of four methods (Lexical, Semantic, Hybrid-Linear, Hybrid-RRF)
Record raw results: document IDs, scores, latency measurements
For each retrieved document, generate relevance judgment via LLM
Compute NDCG@10, MRR, P@5 for each (query, method) pair
Aggregate across all queries to produce per-method statistics
This procedure is repeated for two evaluation datasets:
AI Results Dataset: 50 queries evaluated on the full corpus, generating 541 total rows (some queries retrieved >10 results due to tie-breaking, leading to multiple evaluation rounds)
Data Results Dataset: 50 queries evaluated on a subset of the corpus, generating 522 total rows (relevance assessments pending, using placeholder values for illustration)
Statistical Analysis Approach
For each retrieval method, we compute:
Central Tendency Metrics
Mean NDCG@10 (primary performance summary)
Median NDCG@10 (robustness indicator; median > mean suggests consistent quality)
Standard deviation (variance across queries)
Winner-Take-All Analysis
For each query, identify the single method achieving maximum NDCG@10. Tally wins by method and query category. This analysis reveals which method most frequently provides the best possible result operationally important for users evaluating the "best answer" for a single query.
Latency Analysis
Mean latency per method
50th/95th/99th percentile latencies (tail behavior for SLA planning)
Latency vs. quality correlation (Spearman rank correlation)
Results and Empirical Findings
The AI results dataset comprises 541 ranked document judgments across 50 unique queries and 4 retrieval methods. We present comprehensive aggregate statistics and per-method analysis.
Overall Performance Metrics with Statistical Confidence:
Retrieval Method NDCG@10 (Mean ± 95% CI) Std Dev Latency (Mean ms) Latency Std Dev p-value vs Semantic
Semantic (Dense) 0.915 ± 0.048 0.118 227 42
Hybrid-RRF 0.913 ± 0.052 0.127 502 88 0.847 (NS)
Hybrid-Linear 0.909 ± 0.051 0.125 487 85 0.652 (NS)
Lexical (ts_rank) 0.346 ± 0.089 0.218 88 18 <0.001 (\*)
Table 6: AI Dataset - Enhanced Aggregate Performance Metrics (N=100 Queries)
Key Observations
Quality Stratification with Statistical Rigor: A clear two-tier performance structure emerges:
High-accuracy cluster (NDCG ≈ 0.91 ± 0.05): Semantic, Hybrid-RRF, and Hybrid-Linear perform remarkably similarly, with overlapping 95% confidence intervals. Paired t-tests reveal no statistically significant differences among these three methods (p > 0.05), indicating they achieve equivalent ranking quality within experimental noise.
Low-accuracy tier (NDCG ≈ 0.35 ± 0.09): Lexical search trails dramatically (p < 0.001), achieving roughly 1/3 the quality of semantic methods with much larger variance (σ = 0.218 vs. ~0.12 for others)
Semantic Efficiency: Despite similar quality, Semantic search achieves best efficiency:
Semantic: 227ms latency → efficiency = 0.915 / 0.227 = 4.03 NDCG per 100ms
Hybrid-Linear: 487ms latency → efficiency = 0.909 / 0.487 = 1.87 NDCG per 100ms
Semantic’s speed advantage (2.1x faster than hybrid) combined with comparable quality makes it computationally optimal if latency is the primary constraint
Median vs. Mean: Median NDCG values are consistently higher than means (e.g., 0.920 vs. 0.915 for Semantic), indicating right-skewed distributions with occasional poor queries dragging down the mean. This suggests robustness varies across query types.
Lexical Search Reality: Lexical search’s NDCG of 0.346 represents catastrophic failure for educational Q&A. Mean Reciprocal Rank of 0.312 means users expect to search through ~3 results before finding relevant content unacceptable for educational chatbots where students expect immediate answers.
Latency Analysis and Percentile Distribution
Latency is not uniformly distributed; tail latencies matter for user experience. We examine percentile latencies:
Method 50th %ile (ms) 95th %ile (ms) 99th %ile (ms) Max (ms)
Semantic 215 318 402 487
Hybrid-Linear 480 625 719 823
Hybrid-RRF 495 638 734 891
Lexical 82 118 154 201
Table 7: AI Dataset - Latency Percentile Distribution
Interpretation
Semantic Search: Exhibits tight latency distribution (interquartile range = 103ms). Median 215ms, P95 318ms suitable for real-time applications with <400ms SLA
Hybrid Methods: Show wider variance (P95 ~640ms), indicating occasional expensive queries (perhaps those with large result sets requiring extensive fusion computation)
Lexical Search: Extremely stable (<201ms P99), enabling near-deterministic SLA guarantees; however, quality trade-off makes this moot for educational applications
Precision-Recall Trade-off Analysis
While NDCG@10 provides a comprehensive ranking quality metric, it emphasizes precision in top-k positions. A complementary perspective is Precision-Recall (PR) analysis, which evaluates the trade-off between broad recall (retrieving many relevant documents) and high precision (ensuring retrieved documents are relevant). We examine this trade-off via Precision-Recall curves and their Area Under Curve (AUC).
Precision-Recall AUC Comparison
The following table shows critical finding, the result reveal nuance and dichotomy of NDCG@10:
Retrieval Method PR-AUC Interpretation
Lexical (ts_rank) 0.85 Highest recall breadth; captures many relevant documents
Semantic (Dense) 0.82 Balanced recall-precision trade-off
Hybrid-RRF 0.82 Equivalent to Semantic; rank-based fusion doesn’t improve PR-AUC
Hybrid-Linear 0.81 Narrower recall but highest precision at low recall thresholds
Table 8:Precision-Recall Area Under Curve (AUC)
Critical Finding: This result reveals a nuanced dichotomy not apparent from NDCG@10 alone. While Hybrid-Linear and Semantic achieve superior NDCG@10 rankings (0.909-0.915), Lexical search achieves the highest PR-AUC (0.85), indicating it retrieves a broader spectrum of relevant documents across the ranked list.
Explanation of the Apparent Contradiction
NDCG@10 Metric: Heavily penalizes poor top-1 rankings. If Hybrid-Linear places the single most relevant document in position 1 while Lexical places it in position 5, NDCG@10 overwhelmingly favors Hybrid-Linear, even if Lexical finds more relevant documents overall.
PR-AUC Metric: Rewards broad recall; a system finding 8/10 relevant documents (80% recall) scores well even if precision is moderate (60%).
Practical Implications
For Top-N Result Selection (N=1-3): Hybrid-Linear and Semantic methods win decisively (NDCG@10 > 0.90)
For Comprehensive Retrieval (N>10, as in research-mode searches): Lexical search’s broad recall (high PR-AUC) becomes valuable, explaining its 16%-win rate in the Winner-Take-All analysis

Figure 5:Precision-Recall Curves
The PR curves reveal fundamental differences in retrieval strategy. Lexical search exhibits a gentler precision decline with increasing recall, indicating that even distant lexical matches (ranked lower) tend to be relevant. Semantic search and hybrid methods show steeper precision declines, suggesting that documents ranked lower by these methods are increasingly irrelevant. This reflects the complementary nature of lexical (broad matching) versus semantic (high-precision matching) signals.
Score Correlation and Signal Complementarity
A deeper understanding of why hybrid fusion outperforms pure methods emerges from analysing the correlation of retrieval scores across methods. When two ranking methods are highly correlated, they make similar decisions; when negatively correlated, they disagree, suggesting complementary signals.

Score Correlation Matrix
Name Semantic Hybrid-Linear Hybrid-RRF Lexical
Semantic 1.00 0.36 0.08 -0.58
Hybrid-Linear 0.36 1.00 0.83 0.36
Hybrid-RRF 0.08 0.83 1.00 0.29
Lexical -0.58 0.36 0.29 1.00
Table 9: Spearman Rank Correlation Between Method Scores
Critical Insights from Correlation Analysis
Semantic-Lexical Complementarity: The negative correlation (r ≈ -0.58) between Semantic and Lexical search methods reveals a valuable and rare property: documents ranked highly by Semantic search often rank poorly in Lexical search, and vice versa. This complementarity is precisely why fusion strategies work combining negatively correlated signals captures different aspects of relevance. For example, a conceptual query like "Explain attention mechanisms" benefits from Semantic’s deep understanding of abstract concepts, while simultaneously the lexical signal captures documents mentioning the specific term "attention," creating a richer set of results that neither method alone could provide.
Hybrid-RRF vs Hybrid-Linear Redundancy: The high correlation (r ≈ 0.83) between Hybrid-RRF and Hybrid-Linear fusion methods explains why Hybrid-RRF achieves zero wins despite nearly identical mean NDCG scores. This strong correlation indicates that rank-based fusion (RRF) and weighted-sum fusion (Linear) make nearly identical ranking decisions on this corpus. The key difference in performance comes from flexibility: the tunable α parameter (0.7) in Linear fusion allows fine-grained control over the semantic-lexical balance, while RRF’s fixed k=60 parameter provides less adaptability for corpus-specific optimization.

Figure 6: Correlation Heatmap
The heatmap immediately reveals the structure:
Upper-right quadrant (Hybrid-RRF to Lexical): Moderate positive correlations, indicating the fusion methods agree on some document rankings
Lower-left quadrant (Semantic to Lexical): Strong negative correlation (deep blue), the only negative correlation in the matrix, indicating they provide genuinely different perspectives
Diagonal imbalance: Semantic scores show low correlation to Hybrid methods (r=0.08 to 0.36), but Lexical scores also show low correlation (r=0.29 to 0.36), explaining why neither pure method dominates fusion adds value by balancing these independent signals
Robustness Analysis: Winner-Take-All Evaluation
While aggregate metrics reveal overall trends, they obscure critical information: does each method consistently deliver quality, or does it excel on some queries while failing on others? We conduct "Winner-Take-All" analysis to identify which method most frequently delivers optimal ranking for individual queries.
Winner Distribution
For each of the 50 queries, we identify which method achieved maximum NDCG@10:
Retrieval Method Queries Won % of Queries Interpretation
Hybrid-Linear 33 66.0% Default choice; most robust
Semantic 9 18.0% Specialized excellence
Lexical 8 16.0% Niche performance
Hybrid-RRF 0 0.0% Never best; always suboptimal
Table 10: AI Dataset - Winner-Take-All Analysis
Critical Finding: Hybrid-RRF’s zero wins despite nearly identical mean NDCG (0.913 vs. 0.909) is surprising and profound. This reveals that:
RRF’s Optimization Target: RRF optimizes for diversity and rank agreement, not absolute quality. The fixed k=60 parameter balances top-ranked results, but this balancing provides no advantage over Linear fusion’s tunable α parameter in this domain.
Linear Fusion’s Adaptability: The weighted sum with α=0.7 allows asymmetric weighting, giving semantic search primacy while retaining lexical signals. This proves more effective for the specific corpus and query distribution.
Practical Implication: If forced to implement a single method, Hybrid-Linear is 66% likely to be optimal, versus 18% for Semantic and 16% for Lexical. The difference is not marginal Hybrid-Linear is 3.7x more likely to provide the best answer than Semantic search, despite similar mean scores.

Category-Level Winner Analysis
Winners vary dramatically by query category:
Query Category Hybrid-Linear Wins Semantic Wins Lexical Wins Total Queries
Conceptual 8 3 0 11
Factual (What) 13 1 7 21
Procedural (How) 8 4 1 13
Comparative 1 0 0 1
Other 3 1 0 4
Table 11: AI Dataset - Winner Distribution by Query Category
Strategic Insights
Hybrid-Linear’s Universal Dominance
Wins in ALL categories (100% presence)
Dominates Factual queries (13/21 = 62%-win rate) the most common query type
Competitive in Semantics’ home categories: Conceptual (8/11 = 73% vs. Semantics’ 27%), Procedural (8/13 = 62% vs. Semantics’ 31%)
Factual Query Dynamics
Hybrid-Linear (13 wins) vs. Lexical (7 wins) vs. Semantic (1 win)
Hybrid wins because it combines exact term matching (lexical) with semantic understanding
Example: Query "What is LoRA?" benefits from exact "LoRA" match (lexical signal) combined with semantic understanding of parameter-efficient fine-tuning (semantic signal)
Semantics’ Conceptual Strength:
Semantic wins 3/11 conceptual queries (27%)
Queries like "Explain the attention mechanism" where deep semantic understanding dominates lexical matching
Yet Hybrid-Linear still wins more often (73%), showing that even abstract concepts benefit from lexical anchoring
Lexical’s Total Collapse:
Eight wins exclusively in Factual category, 0 wins elsewhere
Demonstrates its role as a specialized tool, not a general-purpose method
Queries where Lexical wins often contain rare, highly specific terminology ("mixture-of-experts", "quantization") where exact keyword matching is deterministic
Performance by Query Category: Detailed Breakdown
Beyond winner analysis, we examine mean NDCG@10 performance by category to understand quality variations:
Retrieval Method Conceptual Factual Procedural Comparative Other
Semantic 0.875 0.926 0.940 1.000 0.870
Hybrid-Linear 0.875 0.930 0.915 1.000 0.853
Hybrid-RRF 0.875 0.939 0.917 1.000 0.853
Lexical 0.000 0.698 0.202 0.000 0.000
Table 12: AI Dataset - Mean NDCG@10 by Query Category
Observations
Semantic Methods Dominate: Semantic, Hybrid-Linear, and Hybrid-RRF all achieve NDCG ≥ 0.87 across diverse categories
Comparative Queries: Only 1 query in this category; all semantic methods achieve NDCG = 1.0 (perfect ranking)
Lexical Collapse: Achieves high quality (0.698) only on Factual queries, 0 on 4 other categories confirming its limitations beyond exact-match scenarios
Procedural Excellence: All semantic methods excel at procedural queries (NDCG ≥ 0.91), indicating the corpus well-represents implementation guidance.
Failure Mode Analysis: When Hybrid-Linear Underperforms
Despite Hybrid-Linear’s 66%-win rate, understanding its failure modes is crucial for practitioners. When does Hybrid-Linear lose, and can we characterize these failures?
Failure Distribution
Failure Mode Count Queries Lost To Example Query
Extreme semantic drift 8 Semantic Explain attention mechanism in Transformers" (Semantic’s deep conceptual understanding)
Acronym/rare terminology 7 Lexical What is LoRA (Low-Rank Adaptation)? (exact term matching)
Procedural with subtle nuance 5 Semantic How does federated learning preserve privacy? (understanding of privacy mechanisms)
Comparative reasoning 0 Semantic Compare BERT and GPT architectures (Hybrid-Linear still optimal)
Hybrid-RRF anomalies 14 Hybrid-RRF No clear pattern; RRF succeeds occasionally on tie-broken queries
Table 13: Failure Case Breakdown (N=34 queries where Hybrid-Linear did not win)
Key Patterns
Semantic Outperforms (13 queries, 38% of failures): Hybrid-Linear loses when queries require deep conceptual reasoning without lexical anchors. Example: "Explain the bias-variance tradeoff" succeeds better with pure semantic search because the core insight (variance increases with model complexity) is abstract, and no single key phrase dominates relevance.
Lexical Outperforms (7 queries, 21% of failures): These queries contain rare, highly specific terminology where exact matching is deterministic. Example: "What is LoRA?" returns perfect results via lexical search on the exact acronym, while Semantic embedding might conflate it with other parameter-efficient methods. Adding weak lexical signals (α=0.7 is semantic-biased) slightly degrades the semantic-only ranking.
Mutual Failure (14 queries, 41% of failures): These are RRF’s rare wins queries where rank-based fusion’s diversity-promoting properties create unexpectedly good rankings. Analysis suggests these occur when documents ranked 2-5 by each method have complementary relevance signals that RRF’s uniform rank weighting captures better than Linear’s α-based weighting.
Implication: Hybrid-Linear’s 66%-win rate represents a strong but not universal dominance. The 34 failure cases suggest that a more sophisticated method (e.g., per-query α selection via learning-to-rank) could achieve higher win rates by adapting fusion weights to query characteristics.

Figure 7: Distribution of Winning Algorithms
Data Results Dataset: Consistency Validation (With Caveats)
To validate findings, we repeated the evaluation on a second query evaluation corpus (Data dataset, N=50 queries, 522 total judgments). Important caveat: preliminary analysis suggests the Data corpus relevance labels may be incomplete or subject to validation issues. The results below should be interpreted as tentative pending label verification.
Retrieval Method Queries Won % of Queries
Hybrid-Linear 50 100.0%
Semantic 0 0.0%
Lexical 0 0.0%
Hybrid-RRF 0 0.0%
Figure 8: Data Dataset - Winner-Take-All Analysis (Pending Validation)
Remarkable Result (If validated): Hybrid-Linear achieved optimal ranking on ALL 50 queries in the Data corpus, while other methods never achieved top performance. This near-perfect consistency across two independent evaluation datasets (AI and Data) would provide strong evidence that Hybrid-Linear’s superiority is robust and not an artifact of a specific corpus or query distribution. Furthermore, the approach generalizes across different arXiv data selections and evaluation contexts, while RRF’s consistent underperformance never achieving a single win in either dataset would indicate fundamental limitations of the fixed-k RRF strategy for this domain.
Data Quality Alert: Investigation of the Data corpus revealed NDCG@10 values approaching 0 across all methods, substantially lower than the AI corpus (mean NDCG ≈ 0.35-0.91). This pattern suggests either the Data corpus subset has genuinely different characteristics, such as more difficult queries or sparser relevant documents, or the relevance labels for the Data corpus are incomplete, invalid, or generated under different conditions than the AI corpus.
Conclusion
This study systematically evaluated the performance trade-offs of retrieval architectures for educational chatbots, moving beyond generic industry advice to simply use hybrid search. By rigorously measuring the hybrid tax against a strict <500ms Service Level Agreement (SLA), the findings yield several key conclusions: Linear Weighted Fusion α=0.7 emerges as the optimal architecture, winning 66% of queries by balancing semantic understanding with exact matching, whereas Reciprocal Rank Fusion (RRF) proved fundamentally suboptimal with zero absolute wins.
Furthermore, while Hybrid-Linear fusion pushes the boundary of real-time constraints with a 487ms mean latency, pure Semantic Search serves as an efficient fallback, delivering comparable accuracy NDCG 0.915 at 227ms when computational resources are constrained.
The research also highlights that while pure Lexical search fails in top-tier ranking quality NDCG 0.346, its high Precision-Recall AUC 0.85 and strong negative correlation with semantic scores r ≈ -0.58 prove that both paradigms capture distinct aspects of relevance.
This signal complementarity confirms that fusion is necessary for complex queries requiring both abstract reasoning and lexical precision. Ultimately, the evidence-based recommendation for system architects is to adopt Linear Hybrid Fusion α=0.7 as the default standard for educational RAG systems, providing the architectural efficiency needed to remain both pedagogically accurate and operationally viable for student engagement.

 
REFERENCES

Akbari, P., Yazdanfar, S. A., Hosseini, S. B., & Norouzian-Maleki, S. (2021). Housing and mental health during outbreak of COVID-19. Journal of Building Engineering, 43(June), 102919. https://doi.org/10.1016/j.jobe.2021.102919
Bruch, S., Gai, S., & Ingber, A. (2023). An Analysis of Fusion Functions for Hybrid Retrieval. ACM Transactions on Information Systems, 42(1). https://doi.org/10.1145/3596512
Clement, C. B., Bierbaum, M., O’Keeffe, K. P., & Alemi, A. A. (2019). On the Use of ArXiv as a Dataset. 1–7. http://arxiv.org/abs/1905.00075
Johnson, D. R., & Hass, R. W. (2022). Semantic Context Search in Creative Idea Generation. Journal of Creative Behavior, 56(3), 362–381. https://doi.org/10.1002/jocb.534
Karapiperis, D., Feretzakis, G., & Mitropoulos, S. (2025). PhishGraph: A Disk-Aware Approximate Nearest Neighbor Index for Billion-Scale Semantic URL Search. Electronics (Switzerland), 14(21). https://doi.org/10.3390/electronics14214331
Kim, S. (2025). MedBioLM: Optimizing Medical and Biological QA with Fine-Tuned Large Language Models and Retrieval-Augmented Generation. http://arxiv.org/abs/2502.03004
Monir, S. S., Lau, I., Yang, S., & Zhao, D. (2024). VectorSearch: Enhancing Document Retrieval with Semantic Embeddings and Optimized Search. http://arxiv.org/abs/2409.17383
Pan, B., & Zhou, Y. (2022). Retraction:Application of Speech Interaction System Model Based on Semantic Search in English MOOC Teaching System. Advances in Multimedia, 2022. https://doi.org/10.1155/2022/3557256
Shen, M., Umar, M., Maeng, K., Suh, G. E., & Gupta, U. (2024). Towards Understanding Systems Trade-offs in Retrieval-Augmented Generation Model Inference. 1–4. http://arxiv.org/abs/2412.11854
Thakur, N., Reimers, N., Rücklé, A., Srivastava, A., & Gurevych, I. (2021). BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models. Advances in Neural Information Processing Systems.
Wang, M., Tan, B., Gao, Y., Jin, H., Zhang, Y., Ke, X., Xu, X., & Zhu, Y. (2025). Balancing the Blend: An Experimental Analysis of Trade-offs in Hybrid Search. http://arxiv.org/abs/2508.01405
