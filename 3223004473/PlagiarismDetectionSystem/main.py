import sys
import jieba
import numpy as np
from difflib import SequenceMatcher

# 全局配置
JACCARD_WEIGHT= 0.2  # Jaccard初筛阈值
COSINE_WEIGHT = 0.5  # 余弦相似度权重
LCS_WEIGHT = 0.5  # LCS权重

#读取文件内容
def read_file(file_path):
    import os
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在，请检查路径.")
        sys.exit(1)
    try:
        content = ""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                content += line.strip()
        return content
    except Exception as e:
        print(f"文件读取失败: {e}")
        sys.exit(1)

# 文本预处理
def preprocess(text, use_stopwords=True):
    # 停用词表（可根据需求扩展）
    stopwords = {'，', '。', '的', '了', '是', '我', '要', '在', '于', '和', '而且', '或者', '着', '得', '他', '她', '它', '他们', '一个', '一些', '这个', '那个', '啊', '呀', '呢', '吧'} if use_stopwords else set()
    words = jieba.lcut(text)
    return [word for word in words if word not in stopwords and len(word) > 1]


# 相似度计算
def jaccard_similar(set1, set2):
    """Jaccard"""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0.0


def cosine_similar(vec1, vec2):
    """余弦相似度"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2 + 1e-8)  # 防止除以0


def lcs_similar(seq1, seq2):
    """LCS"""
    matcher = SequenceMatcher(None, seq1, seq2)
    return matcher.ratio()


# 综合相似度计算流程
def hybrid_similarity(orig_text, copy_text):
    orig_preprocessed = preprocess(orig_text, use_stopwords=True)
    copy_preprocessed = preprocess(copy_text, use_stopwords=True)
    # Jaccard快速初筛
    orig_set = set(orig_preprocessed)
    copy_set = set(copy_preprocessed)
    jaccard = jaccard_similar(orig_set, copy_set)
    if jaccard < JACCARD_WEIGHT:
        return 0.0

    # 预处理
    orig_tokens = preprocess(orig_text, use_stopwords=False)
    copy_tokens = preprocess(copy_text, use_stopwords=False)

    # 构建余弦相似度向量
    vocabulary = list(set(orig_tokens + copy_tokens))
    vec_orig = np.array([orig_tokens.count(word) for word in vocabulary])
    vec_copy = np.array([copy_tokens.count(word) for word in vocabulary])

    # 并行计算
    cosine = cosine_similar(vec_orig, vec_copy)
    lcs = lcs_similar(orig_tokens, copy_tokens)

    # 加权综合结果
    return (cosine * COSINE_WEIGHT) + (lcs * LCS_WEIGHT)


def main():
    if len(sys.argv) != 4:
        print("请输入程序、原始文件路径、抄袭文件路径、答案文件路径作为命令行参数.")
        return

    orig_path, copy_path, ans_path = sys.argv[1], sys.argv[2], sys.argv[3]

    # 读取原始文本
    orig_text = read_file(orig_path)
    copy_text = read_file(copy_path)

    # 计算混合相似度
    similarity = hybrid_similarity(orig_text, copy_text)
    result = round(similarity, 2)

    # 写入结果文件
    with open(ans_path, 'w', encoding='utf-8') as f:
        f.write(f"{result:.2f}")


if __name__ == "__main__":
    main()
