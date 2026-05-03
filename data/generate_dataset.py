import csv
import random

random.seed(42)

titles = [
    ("Attention Is All You Need", "NLP"),
    ("BERT: Pre-training of Deep Bidirectional Transformers", "NLP"),
    ("GPT-3: Language Models are Few-Shot Learners", "NLP"),
    ("Deep Residual Learning for Image Recognition", "Computer Vision"),
    ("ImageNet Classification with Deep CNNs", "Computer Vision"),
    ("YOLO: Real-Time Object Detection", "Computer Vision"),
    ("Generative Adversarial Networks", "Machine Learning"),
    ("Dropout: Preventing Overfitting in Neural Networks", "Machine Learning"),
    ("Adam: A Method for Stochastic Optimization", "Machine Learning"),
    ("MapReduce: Simplified Data Processing", "Systems"),
    ("Dynamo: Amazon's Highly Available Key-Value Store", "Systems"),
    ("The Google File System", "Systems"),
    ("A Fast Algorithm for Approximate Nearest Neighbors", "Theory"),
    ("Randomized Algorithms for Matrices", "Theory"),
    ("On the Computational Complexity of Neural Networks", "Theory"),
    ("Transformer-XL: Attentive Language Models", "NLP"),
    ("RoBERTa: A Robustly Optimized BERT Approach", "NLP"),
    ("XLNet: Generalized Autoregressive Pretraining", "NLP"),
    ("EfficientNet: Rethinking Model Scaling for CNNs", "Computer Vision"),
    ("Vision Transformer: An Image is Worth 16x16 Words", "Computer Vision"),
    ("CLIP: Learning Transferable Visual Models", "Computer Vision"),
    ("Federated Learning: Strategies for Improving Communication", "Machine Learning"),
    ("Neural Architecture Search with Reinforcement Learning", "Machine Learning"),
    ("XGBoost: A Scalable Tree Boosting System", "Machine Learning"),
    ("Kubernetes: Large-Scale Cluster Management", "Systems"),
    ("Raft: A Consensus Algorithm for Replicated Logs", "Systems"),
    ("Cassandra: A Decentralized Structured Storage System", "Systems"),
    ("PAC Learning: A Framework for Machine Learning Theory", "Theory"),
    ("Lower Bounds for Quantum Computation", "Theory"),
    ("Graph Neural Networks: A Review", "Machine Learning"),
    ("Semantic Segmentation with Fully Convolutional Networks", "Computer Vision"),
    ("Named Entity Recognition with Bidirectional LSTM", "NLP"),
    ("T5: Exploring Limits of Transfer Learning", "NLP"),
    ("DALL-E: Creating Images from Text", "Computer Vision"),
    ("Stable Diffusion: High-Resolution Image Synthesis", "Computer Vision"),
    ("Reinforcement Learning from Human Feedback", "Machine Learning"),
    ("Proximal Policy Optimization Algorithms", "Machine Learning"),
    ("Spanner: Google's Globally Distributed Database", "Systems"),
    ("Bigtable: A Distributed Storage System", "Systems"),
    ("VC Dimension and Sample Complexity", "Theory"),
    ("Word2Vec: Distributed Representations of Words", "NLP"),
    ("GloVe: Global Vectors for Word Representation", "NLP"),
    ("ResNeXt: Aggregated Residual Transformations", "Computer Vision"),
    ("DenseNet: Densely Connected Networks", "Computer Vision"),
    ("CycleGAN: Image-to-Image Translation", "Computer Vision"),
    ("WGAN: Wasserstein GAN", "Machine Learning"),
    ("Batch Normalization: Accelerating Deep Network Training", "Machine Learning"),
    ("LightGBM: A Highly Efficient Gradient Boosting Decision Tree", "Machine Learning"),
    ("ZooKeeper: Wait-free Coordination for Internet-scale Systems", "Systems"),
    ("Approximation Algorithms for NP-Hard Problems", "Theory"),
]

abstracts = [
    "We propose a novel architecture based on attention mechanisms that achieves state-of-the-art results on several benchmarks. Our model demonstrates significant improvements over existing methods in terms of both accuracy and computational efficiency. Extensive experiments validate the effectiveness of the proposed approach across multiple datasets.",
    "This paper presents a comprehensive study of deep learning methods applied to large-scale datasets. We introduce new techniques for training neural networks and demonstrate their superior performance on standard benchmarks. The proposed framework is both scalable and efficient, making it suitable for real-world applications.",
    "We introduce a new method for unsupervised representation learning that outperforms existing approaches. The model leverages self-supervised objectives to learn meaningful features from raw data without manual annotation. Results on downstream tasks confirm the quality of the learned representations.",
    "In this work, we address the challenge of efficient computation in distributed systems. Our approach reduces communication overhead while maintaining strong consistency guarantees. We provide theoretical analysis and empirical results on large-scale deployments.",
    "We present theoretical foundations for a new class of algorithms with provable guarantees. The analysis reveals fundamental trade-offs between time complexity and approximation quality. Applications to practical problems demonstrate the utility of our framework.",
    "This paper explores the intersection of language modeling and knowledge representation. We show that pre-trained language models implicitly encode factual knowledge that can be extracted for downstream tasks. Fine-tuning strategies are proposed to better leverage this knowledge.",
    "We study the problem of generalization in machine learning models trained on limited data. Novel regularization techniques are proposed that significantly reduce overfitting. Extensive ablation studies confirm the contribution of each component.",
    "Our work introduces a new benchmark for evaluating natural language understanding systems. We collect data from diverse sources and validate annotations through rigorous quality control. Baseline results establish clear directions for future research.",
    "This paper addresses scalability challenges in modern distributed databases. We propose new indexing strategies that support high-throughput workloads while maintaining ACID guarantees. Performance evaluations on real-world workloads demonstrate significant speedups.",
    "We propose a graph-based approach to relational reasoning that captures structural dependencies. Message passing algorithms are designed to propagate information efficiently through the graph. Results on relational datasets show improvements over baselines.",
]

rows = []
paper_id = 1

for i, (title, category) in enumerate(titles):
    abstract = abstracts[i % len(abstracts)]
    year = random.randint(2015, 2024)
    citations = int(random.expovariate(1/500))
    citations = min(citations, 5000)
    keywords = random.randint(3, 12)
    rows.append({
        "id": paper_id,
        "title": title,
        "abstract": abstract,
        "year": year,
        "citations": citations,
        "keywords": keywords,
        "category": category,
    })
    paper_id += 1

# Add some extras with variations
extra_titles = [
    ("Self-Supervised Contrastive Learning", "Machine Learning"),
    ("Zero-Shot Learning via Semantic Embeddings", "NLP"),
    ("Pose Estimation Using Heatmap Regression", "Computer Vision"),
    ("Distributed Training of Large Language Models", "Systems"),
    ("Information Theoretic Bounds for Learning", "Theory"),
    ("Multimodal Fusion for Sentiment Analysis", "NLP"),
    ("Point Cloud Processing with PointNet", "Computer Vision"),
    ("Meta-Learning: Learning to Learn", "Machine Learning"),
    ("Byzantine Fault Tolerance in Distributed Systems", "Systems"),
    ("Kolmogorov Complexity and Learning Theory", "Theory"),
]

for title, category in extra_titles:
    abstract = abstracts[random.randint(0, len(abstracts)-1)]
    year = random.randint(2016, 2024)
    citations = int(random.expovariate(1/300))
    citations = min(citations, 3000)
    keywords = random.randint(4, 10)
    rows.append({
        "id": paper_id,
        "title": title,
        "abstract": abstract,
        "year": year,
        "citations": citations,
        "keywords": keywords,
        "category": category,
    })
    paper_id += 1

with open("papers.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["id", "title", "abstract", "year", "citations", "keywords", "category"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} papers → papers.csv")
