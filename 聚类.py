import pandas as pd
import numpy as np
from sklearn.cluster import AgglomerativeClustering
import jieba
import re
from collections import Counter, defaultdict
import matplotlib.pyplot as plt

class ImprovedLabelClusterer:
    def __init__(self, similarity_threshold=0.4):
        """
        改进的标签聚类器，专门针对中文短文本优化
        """
        self.similarity_threshold = similarity_threshold
        self.label_clusters = {}
        self.cluster_representatives = {}
        
        # 语义同义词典
        self.semantic_dict = {
            # 跑步相关
            '跑步': ['晨跑', '夜跑', '慢跑', '长跑'],
            '早晨': ['早上', '上午', '晨'],
            '晚上': ['夜晚', '夜', '傍晚'],
            
            # 机场相关
            '候机': ['等待', '等候'],
            '机场': ['航站楼', '候机厅'],
            
            # 购物相关
            '购物': ['逛街', '买东西', 'shopping'],
            '商场': ['商城', '购物中心', '百货'],
            
            # 观影相关
            '看电影': ['观影', '看片'],
            '电影院': ['影院', '电影城'],
            
            # 咖啡相关
            '咖啡厅': ['咖啡店', '咖啡馆'],
            
            # 健身相关
            '健身': ['运动', '锻炼', '训练'],
            '健身房': ['gym'],
            
            # 工作相关
            '上班': ['工作', '办公'],
        }
    
    def preprocess_labels(self, labels):
        """预处理标签"""
        unique_labels = list(set([str(label).strip() for label in labels if pd.notna(label) and str(label).strip()]))
        cleaned_labels = []
        for label in unique_labels:
            cleaned = re.sub(r'[^\w\s\u4e00-\u9fff]', '', label)
            if cleaned:
                cleaned_labels.append(cleaned)
        return cleaned_labels
    
    def extract_keywords(self, text):
        """提取文本关键词"""
        words = list(jieba.cut(text))
        # 过滤停用词和单字符
        keywords = [w for w in words if len(w) > 1 or w in '早晚上下中']
        return keywords
    
    def levenshtein_distance(self, s1, s2):
        """计算编辑距离"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def char_similarity(self, s1, s2):
        """基于字符的相似度"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        edit_dist = self.levenshtein_distance(s1, s2)
        return 1 - (edit_dist / max_len)
    
    def semantic_similarity(self, label1, label2):
        """语义相似度计算"""
        words1 = self.extract_keywords(label1)
        words2 = self.extract_keywords(label2)
        
        # 完全匹配
        if label1 == label2:
            return 1.0
        
        # 检查是否有直接的同义词关系
        for word1 in words1:
            for word2 in words2:
                # 检查同义词典
                for key, synonyms in self.semantic_dict.items():
                    if (word1 == key and word2 in synonyms) or \
                       (word2 == key and word1 in synonyms) or \
                       (word1 in synonyms and word2 in synonyms):
                        return 0.8
                
                # 检查包含关系
                if word1 in word2 or word2 in word1:
                    return 0.7
        
        # 计算词汇重叠度
        words1_set = set(words1)
        words2_set = set(words2)
        if words1_set and words2_set:
            intersection = len(words1_set & words2_set)
            union = len(words1_set | words2_set)
            jaccard = intersection / union if union > 0 else 0
            if jaccard > 0:
                return 0.6 + jaccard * 0.3
        
        # 字符相似度
        char_sim = self.char_similarity(label1, label2)
        
        # 特殊规则匹配
        similarity_score = self.rule_based_similarity(label1, label2)
        if similarity_score > 0:
            return max(similarity_score, char_sim)
        
        return char_sim
    
    def rule_based_similarity(self, label1, label2):
        """基于规则的相似度判断"""
        # 跑步相关规则
        running_patterns = ['跑步', '跑', '晨跑', '夜跑']
        morning_patterns = ['早晨', '早上', '晨', '上午']
        
        # 检查跑步+时间组合
        has_running_1 = any(p in label1 for p in running_patterns)
        has_running_2 = any(p in label2 for p in running_patterns)
        has_morning_1 = any(p in label1 for p in morning_patterns)
        has_morning_2 = any(p in label2 for p in morning_patterns)
        
        if has_running_1 and has_running_2:
            if has_morning_1 and has_morning_2:
                return 0.85  # 都是早晨跑步
            return 0.75  # 都是跑步
        
        # 机场相关规则
        airport_patterns = ['机场', '候机', '等待', '等候']
        airport_count_1 = sum(1 for p in airport_patterns if p in label1)
        airport_count_2 = sum(1 for p in airport_patterns if p in label2)
        
        if airport_count_1 >= 2 and airport_count_2 >= 2:
            return 0.85
        elif airport_count_1 >= 1 and airport_count_2 >= 1:
            return 0.75
        
        # 购物相关规则
        shopping_patterns = ['购物', '逛街', '商场', '买']
        shopping_count_1 = sum(1 for p in shopping_patterns if p in label1)
        shopping_count_2 = sum(1 for p in shopping_patterns if p in label2)
        
        if shopping_count_1 >= 1 and shopping_count_2 >= 1:
            return 0.8
        
        # 观影相关规则
        movie_patterns = ['电影', '观影', '看电影', '影院']
        movie_count_1 = sum(1 for p in movie_patterns if p in label1)
        movie_count_2 = sum(1 for p in movie_patterns if p in label2)
        
        if movie_count_1 >= 1 and movie_count_2 >= 1:
            return 0.8
        
        # 咖啡相关规则
        coffee_patterns = ['咖啡', '咖啡厅', '咖啡店']
        coffee_count_1 = sum(1 for p in coffee_patterns if p in label1)
        coffee_count_2 = sum(1 for p in coffee_patterns if p in label2)
        
        if coffee_count_1 >= 1 and coffee_count_2 >= 1:
            return 0.8
        
        # 健身相关规则
        fitness_patterns = ['健身', '运动', '锻炼', '健身房']
        fitness_count_1 = sum(1 for p in fitness_patterns if p in label1)
        fitness_count_2 = sum(1 for p in fitness_patterns if p in label2)
        
        if fitness_count_1 >= 1 and fitness_count_2 >= 1:
            return 0.8
        
        return 0
    
    def compute_similarity_matrix(self, labels):
        """计算相似度矩阵"""
        n = len(labels)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    similarity_matrix[i][j] = self.semantic_similarity(labels[i], labels[j])
        
        return similarity_matrix
    
    def cluster_labels(self, labels):
        """聚类标签"""
        print(f"开始处理 {len(labels)} 个唯一标签...")
        
        cleaned_labels = self.preprocess_labels(labels)
        print(f"清洗后剩余 {len(cleaned_labels)} 个标签")
        
        if len(cleaned_labels) < 2:
            return {label: [label] for label in cleaned_labels}
        
        # 计算相似度矩阵
        similarity_matrix = self.compute_similarity_matrix(cleaned_labels)
        
        # 转换为距离矩阵
        distance_matrix = 1 - similarity_matrix
        
        # 层次聚类
        distance_threshold = 1 - self.similarity_threshold
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=distance_threshold,
            linkage='average',
            metric='precomputed'
        )
        
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # 组织聚类结果
        clusters = defaultdict(list)
        for i, cluster_id in enumerate(cluster_labels):
            clusters[cluster_id].append(cleaned_labels[i])
        
        # 选择代表性标签（最短的）
        cluster_representatives = {}
        for cluster_id, cluster_members in clusters.items():
            representative = min(cluster_members, key=len)
            cluster_representatives[cluster_id] = representative
        
        # 创建标签映射
        label_mapping = {}
        for cluster_id, cluster_members in clusters.items():
            representative = cluster_representatives[cluster_id]
            for member in cluster_members:
                label_mapping[member] = representative
        
        self.label_clusters = dict(clusters)
        self.cluster_representatives = cluster_representatives
        
        return label_mapping, dict(clusters)
    
    def apply_clustering_to_dataframe(self, df, column_name='场景', new_column_name='标准化场景'):
        """将聚类结果应用到DataFrame"""
        all_labels = df[column_name].dropna().astype(str).tolist()
        label_mapping, clusters = self.cluster_labels(all_labels)
        
        df[new_column_name] = df[column_name].map(
            lambda x: label_mapping.get(str(x).strip(), str(x)) if pd.notna(x) else x
        )
        
        return df, label_mapping, clusters

# 演示函数
def demo_usage():
    """演示使用"""
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
    print("原始数据场景分布:")
    print(df['场景'].value_counts())
    print("\n" + "="*60 + "\n")
    
    # 使用改进的聚类器
    clusterer = ImprovedLabelClusterer(similarity_threshold=0.4)
    
    # 执行聚类
    df_clustered, label_mapping, clusters = clusterer.apply_clustering_to_dataframe(df)
    
    print("聚类后的场景分布:")
    print(df_clustered['标准化场景'].value_counts())
    print("\n" + "="*60 + "\n")
    
    print("标签映射关系:")
    for original, standardized in sorted(label_mapping.items()):
        if original != standardized:
            print(f"  {original} -> {standardized}")
    print()
    
    print("聚类详情:")
    for i, (cluster_id, members) in enumerate(clusters.items()):
        if len(members) > 1:
            representative = clusterer.cluster_representatives[cluster_id]
            print(f"  聚类 {i+1} (代表: {representative}): {members}")
    
    # 显示相似度计算详情
    print(f"\n" + "="*30 + " 相似度详情 " + "="*30)
    unique_labels = list(set(df['场景'].tolist()))
    cleaned_labels = clusterer.preprocess_labels(unique_labels)
    
    print("高相似度标签对:")
    similarity_matrix = clusterer.compute_similarity_matrix(cleaned_labels)
    high_sim_pairs = []
    
    for i in range(len(cleaned_labels)):
        for j in range(i+1, len(cleaned_labels)):
            sim = similarity_matrix[i][j]
            if sim >= clusterer.similarity_threshold:
                high_sim_pairs.append((cleaned_labels[i], cleaned_labels[j], sim))
    
    for label1, label2, sim in sorted(high_sim_pairs, key=lambda x: x[2], reverse=True):
        print(f"  {label1} <-> {label2}: {sim:.3f}")
    
    return df_clustered, label_mapping, clusters

# 处理CSV文件的函数
def process_csv_file(file_path, column_name='场景', similarity_threshold=0.4):
    """处理实际的CSV文件"""
    df = pd.read_csv(file_path, encoding='utf-8')
    print(f"读取到 {len(df)} 行数据")
    print(f"场景列有 {df[column_name].nunique()} 个唯一值")
    
    clusterer = ImprovedLabelClusterer(similarity_threshold=similarity_threshold)
    df_clustered, label_mapping, clusters = clusterer.apply_clustering_to_dataframe(df, column_name)
    
    # 保存结果
    output_file = file_path.replace('.csv', '_clustered.csv')
    df_clustered.to_csv(output_file, index=False, encoding='utf-8')
    
    # 保存映射关系
    mapping_file = file_path.replace('.csv', '_label_mapping.txt')
    with open(mapping_file, 'w', encoding='utf-8') as f:
        f.write("标签映射关系:\n")
        f.write("="*50 + "\n")
        for original, standardized in sorted(label_mapping.items()):
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
    print("=== 改进版语义聚类演示 ===")
    demo_usage()
    
    print(f"\n{'='*80}")
    print("使用说明:")
    print("process_csv_file('your_file.csv', column_name='场景', similarity_threshold=0.4)")
    print("- similarity_threshold: 建议0.3-0.5，越低聚类越宽松")