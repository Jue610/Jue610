import unittest
import sys
import jieba
import numpy as np
from difflib import SequenceMatcher


# 全局配置
jaccard_weight = 0.2  # Jaccard初筛阈值
cosine_weight = 0.5  # 余弦相似度权重
lcs_weight = 0.5  # LCS权重


# 读取文件内容
def read_file(file_path):
    import os
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在，请检查路径.")
    try:
        content = ""
        with open(file_path, 'r', encoding='utf - 8') as f:
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
    return [word for word in words if word not in stopwords and len(word)>1]


# 相似度计算
def jaccard_similar(set1, set2):
    """Jaccard"""
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    if union == 0:
        # 这里不再打印可能造成混淆的信息
        return 0.0
    return intersection / union if union!= 0 else 0.0


def cosine_similar(vec1, vec2):
    """余弦相似度"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    if norm1 * norm2 == 0:
        # 这里不再打印可能造成混淆的信息
        return 0.0
    return dot_product / (norm1 * norm2 + 1e-8)  # 防止除以0


def lcs_similar(seq1, seq2):
    """LCS"""
    matcher = SequenceMatcher(None, seq1, seq2)
    return matcher.ratio()


# 综合相似度计算流程
def hybrid_similarity(orig_text, copy_text):
    orig_preprocessed = preprocess(orig_text, use_stopwords=True)
    copy_preprocessed = preprocess(copy_text, use_stopwords=True)
    # 特殊情况，如果原始文本和抄袭文本都为空
    if not orig_preprocessed and not copy_preprocessed:
        return 0.0
    # Jaccard快速初筛
    orig_set = set(orig_preprocessed)
    copy_set = set(copy_preprocessed)
    jaccard = jaccard_similar(orig_set, copy_set)
    if jaccard < jaccard_weight:
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
    return (cosine * cosine_weight)+(lcs * lcs_weight)


class TestSimilarity(unittest.TestCase):
    def test_same_text(self):
        orig_text = "这是一个测试文本"
        copy_text = "这是一个测试文本"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(round(similarity, 2), 1.00)

    def test_empty_text(self):
        orig_text = ""
        copy_text = ""
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(round(similarity, 2), 0.00)

    def test_only_stopwords_text(self):
        orig_text = "的是了"
        copy_text = "的是了"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(round(similarity, 2), 0.00)

    def test_jaccard_not_pass(self):
        orig_text = "今天天气很好"
        copy_text = "明天天气不好"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(round(similarity, 2), 0.00)

    def test_jaccard_pass_cosine_zero(self):
        orig_text = "我喜欢苹果"
        copy_text = "我喜欢香蕉"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertTrue(similarity < 1.00)

    def test_jaccard_pass_lcs_zero(self):
        orig_text = "红色的花朵"
        copy_text = "蓝色的天空"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(type(similarity), float)
        self.assertTrue(similarity < 1.00)

    def test_cosine_special_case(self):
        orig_text = "，，，，，，，，，，"
        copy_text = "。。。。。。。。。。"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(type(similarity), float)
        self.assertTrue(similarity < 1.00)

    def test_jaccard_special_case(self):
        orig_text = "####"
        copy_text = "$$$$"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertEqual(round(similarity, 2), 0.00)

    def test_long_text(self):
        orig_text = "这是一篇很长的新闻报道，包含很多信息，讲述了一个有趣的故事。"
        copy_text = "这是一篇很长的新闻报道，有部分信息被修改，讲述了一个有趣的故事。"
        similarity = hybrid_similarity(orig_text, copy_text)
        self.assertTrue(similarity < 1.00)

    def test_non_existent_path(self):
        non_existent_path = "non_existent_folder/non_existent_file.txt"
        with self.assertRaises(FileNotFoundError):
            read_file(non_existent_path)

if __name__ == '__main__':
    unittest.main()