import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import AgglomerativeClustering
import jieba
import re
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns

class LabelClusterer:
    def __init__(self, similarity_threshold=0.6):
        """
        初始化标签聚类器
        similarity_threshold: 相似度阈值，用于判断是否为同一类
        """
        self.similarity_threshold = similarity_threshold
        self.label_clusters = {}
        self.cluster_representatives = {}
        
    def preprocess_labels(self, labels):
        """
        预处理标签：去重、清洗、分词
        """
        # 去除重复和空值
        unique_labels = list(set([str(label).strip() for label in labels if pd.notna(label) and str(label).strip()]))
        
        # 简单清洗：去除特殊字符，保留中文、英文、数字
        cleaned_labels = []
        for label in unique_labels:
            cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', label)
            if cleaned:
                cleaned_labels.append(cleaned)
        
        return cleaned_labels
    
    def extract_features(self, labels):
        """
        提取标签特征：使用TF-IDF和字符级n-gram
        """
        # 中文分词
        segmented_labels = []
        for label in labels:
            # 结合字符级和词级特征
            words = list(jieba.cut(label))
            chars = list(label)
            # 组合词级和字符级特征
            features = words + chars + [label[i:i+2] for i in range(len(label)-1)]
            segmented_labels.append(' '.join(features))
        
        # TF-IDF向量化
        vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 2),
            min_df=1
        )
        
        feature_matrix = vectorizer.fit_transform(segmented_labels)
        return feature_matrix, vectorizer
    
    def compute_similarity_matrix(self, feature_matrix):
        """
        计算标签间的余弦相似度矩阵
        """
        similarity_matrix = cosine_similarity(feature_matrix)
        return similarity_matrix
    
    def cluster_labels(self, labels):
        """
        对标签进行聚类
        """
        print(f"开始处理 {len(labels)} 个唯一标签...")
        
        # 预处理
        cleaned_labels = self.preprocess_labels(labels)
        print(f"清洗后剩余 {len(cleaned_labels)} 个标签")
        
        if len(cleaned_labels) < 2:
            return {label: [label] for label in cleaned_labels}
        
        # 特征提取
        feature_matrix, vectorizer = self.extract_features(cleaned_labels)
        
        # 计算相似度矩阵
        similarity_matrix = self.compute_similarity_matrix(feature_matrix)
        
        # 层次聚类
        # 使用距离阈值进行聚类
        distance_threshold = 1 - self.similarity_threshold
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage='average'
        )
        
        cluster_labels = clustering.fit_predict(similarity_matrix)
        
        # 组织聚类结果
        clusters = {}
        for i, cluster_id in enumerate(cluster_labels):
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(cleaned_labels[i])
        
        # 为每个聚类选择代表性标签（最短的或最常见的）
        cluster_representatives = {}
        for cluster_id, cluster_members in clusters.items():
            # 选择最短的标签作为代表
            representative = min(cluster_members, key=len)
            cluster_representatives[cluster_id] = representative
        
        # 创建标签映射
        label_mapping = {}
        for cluster_id, cluster_members in clusters.items():
            representative = cluster_representatives[cluster_id]
            for member in cluster_members:
                label_mapping[member] = representative
        
        self.label_clusters = clusters
        self.cluster_representatives = cluster_representatives
        
        return label_mapping, clusters
    
    def visualize_clusters(self, clusters, top_n=20):
        """
        可视化聚类结果
        """
        # 统计每个聚类的大小
        cluster_sizes = {f"聚类{i}({rep})": len(members) 
                        for i, (cluster_id, members) in enumerate(clusters.items()) 
                        for rep in [self.cluster_representatives[cluster_id]]}
        
        # 只显示前N个最大的聚类
        sorted_clusters = sorted(cluster_sizes.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        plt.figure(figsize=(12, 8))
        names, sizes = zip(*sorted_clusters)
        plt.barh(range(len(names)), sizes)
        plt.yticks(range(len(names)), names)
        plt.xlabel('聚类大小')
        plt.title('标签聚类结果 (Top 20)')
        plt.tight_layout()
        plt.show()
        
        return sorted_clusters
    
    def apply_clustering_to_dataframe(self, df, column_name='场景', new_column_name='标准化场景'):
        """
        将聚类结果应用到DataFrame
        """
        # 获取所有标签
        all_labels = df[column_name].dropna().astype(str).tolist()
        
        # 执行聚类
        label_mapping, clusters = self.cluster_labels(all_labels)
        
        # 应用映射
        df[new_column_name] = df[column_name].map(lambda x: label_mapping.get(str(x).strip(), str(x)) if pd.notna(x) else x)
        
        return df, label_mapping, clusters

# 使用示例
def demo_usage():
    """
    演示如何使用标签聚类器
    """
    # 创建示例数据
    sample_data = {
        '用户ID': range(1, 21),
        '场景': [
            '早晨跑步', '晨跑', '早上跑步', '机场候机', '机场等待', 
            '在机场等候', '购物', '逛街', '商场购物', '看电影',
            '电影院', '观影', '咖啡厅', '喝咖啡', '咖啡店',
            '健身房', '运动', '锻炼', '上班', '工作中'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    print("原始数据:")
    print(df['场景'].value_counts())
    print("\n" + "="*50 + "\n")
    
    # 初始化聚类器
    clusterer = LabelClusterer(similarity_threshold=0.5)
    
    # 执行聚类
    df_clustered, label_mapping, clusters = clusterer.apply_clustering_to_dataframe(df)
    
    # 显示结果
    print("聚类后的数据:")
    print(df_clustered['标准化场景'].value_counts())
    print("\n" + "="*50 + "\n")
    
    print("标签映射关系:")
    for original, standardized in label_mapping.items():
        if original != standardized:
            print(f"{original} -> {standardized}")
    
    print("\n" + "="*50 + "\n")
    
    print("聚类详情:")
    for i, (cluster_id, members) in enumerate(clusters.items()):
        if len(members) > 1:  # 只显示有多个成员的聚类
            representative = clusterer.cluster_representatives[cluster_id]
            print(f"聚类 {i+1} (代表: {representative}): {members}")
    
    return df_clustered, label_mapping, clusters

# 主函数：处理实际CSV文件
def process_csv_file(file_path, column_name='场景', similarity_threshold=0.6):
    """
    处理实际的CSV文件
    """
    # 读取数据
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"读取到 {len(df)} 行数据")
    print(f"场景列有 {df[column_name].nunique()} 个唯一值")
    
    # 初始化聚类器
    clusterer = LabelClusterer(similarity_threshold=similarity_threshold)
    
    # 执行聚类
    df_clustered, label_mapping, clusters = clusterer.apply_clustering_to_dataframe(df, column_name)
    
    # 保存结果
    output_file = file_path.replace('.csv', '_clustered.csv')
    df_clustered.to_csv(output_file, index=False, encoding='utf-8')
    
    # 保存映射关系
    mapping_file = file_path.replace('.csv', '_label_mapping.txt')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("标签映射关系:\n")
        f.write("="*50 + "\n")
        for original, standardized in label_mapping.items():
            if original != standardized:
                f.write(f"{original} -> {standardized}\n")
        
        f.write("\n聚类详情:\n")
        f.write("="*50 + "\n")
        for i, (cluster_id, members) in enumerate(clusters.items()):
            if len(members) > 1:
                representative = clusterer.cluster_representatives[cluster_id]
                f.write(f"聚类 {i+1} (代表: {representative}): {', '.join(members)}\n")
    
    print(f"处理完成！")
    print(f"聚类后的数据保存到: {output_file}")
    print(f"映射关系保存到: {mapping_file}")
    print(f"原始标签数: {df[column_name].nunique()}")
    print(f"聚类后标签数: {df_clustered['标准化场景'].nunique()}")
    
    return df_clustered, label_mapping, clusters

if __name__ == "__main__":
    # 运行演示
    print("=== 演示模式 ===")
    demo_usage()
    
    print("\n\n=== 使用说明 ===")
    print("处理你的CSV文件，请使用:")
    print("df, mapping, clusters = process_csv_file('your_file.csv', column_name='场景', similarity_threshold=0.6)")
    print("\n参数说明:")
    print("- file_path: CSV文件路径")
    print("- column_name: 要聚类的列名（默认'场景'）")
    print("- similarity_threshold: 相似度阈值（0-1，默认0.6，越高越严格）")