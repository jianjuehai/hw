import pandas as pd
import numpy as np
import jieba
from sklearn.cluster import AgglomerativeClustering
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# === 配置参数 ===
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'  # 多语言句向量模型
SIMILARITY_THRESHOLD = 0.85  # 类内最小相似度阈值
CLUSTER_SIMILARITY = 0.75   # 初始聚类相似度阈值

# === 步骤1: 数据加载 ===
df = pd.read_csv('scenes.csv', header=None, names=['text'])
texts = df['text'].tolist()
print(f"待处理文本数量: {len(texts)}")

# === 步骤2: 加载预训练模型 ===
model = SentenceTransformer(MODEL_NAME)
print("模型加载完成，开始文本编码...")

# === 步骤3: 生成句向量 ===
embeddings = model.encode(texts, convert_to_tensor=False)
print("文本向量化完成")

# === 步骤4: 两阶段聚类 ===
# 第一阶段：初步聚类
clustering = AgglomerativeClustering(
    n_clusters=None,
    affinity='cosine',
    linkage='average',
    distance_threshold=1-CLUSTER_SIMILARITY  # 距离阈值=1-相似度
)
clusters = clustering.fit_predict(embeddings)
df['cluster'] = clusters

# 第二阶段：类内精确调整
final_clusters = []
current_cluster_id = 0

for cluster_id in set(clusters):
    cluster_texts = df[df['cluster'] == cluster_id]['text'].tolist()
    cluster_embeddings = model.encode(cluster_texts)
    
    # 计算类内相似度矩阵
    sim_matrix = cosine_similarity(cluster_embeddings)
    
    # 使用连通组件进行子类划分
    visited = set()
    for i in range(len(cluster_texts)):
        if i not in visited:
            # 创建新子类
            new_cluster = [i]
            visited.add(i)
            
            # 查找相似文本
            for j in range(i+1, len(cluster_texts)):
                if sim_matrix[i, j] >= SIMILARITY_THRESHOLD:
                    new_cluster.append(j)
                    visited.add(j)
            
            # 分配新聚类ID
            for idx in new_cluster:
                final_clusters.append((cluster_texts[idx], current_cluster_id))
            current_cluster_id += 1

# === 步骤5: 结果整理 ===
result_df = pd.DataFrame(final_clusters, columns=['text', 'final_cluster'])
result_df = result_df.merge(df[['text', 'cluster']], on='text')
print("聚类完成，生成结果...")

# === 步骤6: 结果验证与输出 ===
# 计算类内相似度统计
cluster_stats = []
for cluster_id in result_df['final_cluster'].unique():
    cluster_texts = result_df[result_df['final_cluster'] == cluster_id]['text'].tolist()
    cluster_emb = model.encode(cluster_texts)
    sim_values = cosine_similarity(cluster_emb)[np.triu_indices(len(cluster_texts), 1)]
    
    cluster_stats.append({
        'cluster_id': cluster_id,
        'text_count': len(cluster_texts),
        'min_similarity': np.min(sim_values) if len(sim_values) > 0 else 1.0,
        'avg_similarity': np.mean(sim_values) if len(sim_values) > 0 else 1.0
    })

stats_df = pd.DataFrame(cluster_stats)
print("\n=== 聚类质量统计 ===")
print(stats_df.describe())

# 保存结果
result_df.to_csv('high_accuracy_clusters.csv', index=False)
print("结果已保存至 high_accuracy_clusters.csv")

# === (可选)人工审核接口 ===
def review_clusters(cluster_id):
    """查看指定聚类的详细内容"""
    cluster_texts = result_df[result_df['final_cluster'] == cluster_id]['text'].tolist()
    print(f"\n聚类 {cluster_id} 包含 {len(cluster_texts)} 个文本:")
    for text in cluster_texts:
        print(f" - {text}")
    
    # 计算类内相似度
    emb = model.encode(cluster_texts)
    sim_matrix = cosine_similarity(emb)
    print(f"\n类内相似度矩阵:")
    print(sim_matrix.round(2))

# 示例：查看聚类0的内容
# review_clusters(0)