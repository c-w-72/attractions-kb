"""
增强检索引擎
- jieba 中文分词
- 字段加权检索 (name×5, highlights×3, province×2, ...)
- TF-IDF 索引磁盘持久化
- LRU 查询缓存
"""

import json
import os
import hashlib
import pickle
from functools import lru_cache
from typing import Optional

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DATA_FILE = os.path.join(DATA_DIR, "attractions.json")
CACHE_DIR = os.path.join(DATA_DIR, "cache")

# 字段权重
FIELD_WEIGHTS = {
    "name": 5.0,
    "highlights": 3.0,
    "province": 2.0,
    "city": 2.0,
    "category": 1.5,
    "description": 1.0,
    "tips": 1.0,
    "food": 1.2,
    "culture": 1.2,
    "basic_info": 1.0,
    "travel_guide": 1.0,
    "transport": 1.0,
}


class AttractionRetriever:
    """增强版旅游景点检索器"""

    def __init__(self, data_path: str = None):
        self.data_path = data_path or DATA_FILE
        self.attractions = self._load_data()
        self._vectorizers = {}  # field -> (vec, matrix)
        self._tokenizer = None
        self._province_index = {}   # province -> [att, ...]
        self._category_index = {}   # category -> [att, ...]
        self._name_index = {}       # name -> att
        self._id_index = {}         # id -> att
        self._build_indices()
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _build_indices(self):
        """预建倒排索引，加速筛选"""
        for a in self.attractions:
            # 省份索引
            p = a["province"]
            if p not in self._province_index:
                self._province_index[p] = []
            self._province_index[p].append(a)

            # 分类索引
            c = a["category"]
            if c not in self._category_index:
                self._category_index[c] = []
            self._category_index[c].append(a)

            # 名称/ID 索引
            self._name_index[a["name"]] = a
            self._id_index[a["id"]] = a

    def _load_data(self) -> list:
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _get_tokenizer(self):
        """延迟加载 jieba 分词器"""
        if self._tokenizer is None:
            import jieba
            jieba.setLogLevel(20)
            self._tokenizer = jieba
            # 加载景点名词典
            for att in self.attractions:
                jieba.add_word(att["name"], freq=100, tag="ns")
                for h in att.get("highlights", "").split("、"):
                    h = h.strip()
                    if len(h) >= 2:
                        jieba.add_word(h, freq=50)
        return self._tokenizer

    def _tokenize(self, text: str) -> str:
        """分词并用空格连接"""
        try:
            tok = self._get_tokenizer()
            return " ".join(tok.cut(text))
        except ImportError:
            return text

    def _build_field_text(self, att: dict, field: str) -> str:
        """构建某个字段的检索文本"""
        raw = att.get(field, "")
        if isinstance(raw, str) and raw:
            if field in ("name", "province", "city", "category"):
                return raw
            return raw
        return ""

    def build_index(self, use_semantic: bool = False):
        """构建索引（自动从缓存加载或重建）"""
        self._build_weighted_tfidf()
        if use_semantic:
            self._try_build_semantic()

    def _build_weighted_tfidf(self):
        """构建加权 TF-IDF 索引，按字段分别向量化"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from scipy import sparse

        cache_path = os.path.join(CACHE_DIR, "weighted_index.pkl")

        # 尝试从缓存加载
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "rb") as f:
                    data = pickle.load(f)
                if data.get("version") == 2 and data.get("count") == len(self.attractions):
                    self._vectorizers = data["vectorizers"]
                    self._weighted_matrix = data["matrix"]
                    self._feature_fields = data["fields"]
                    self._use_semantic = False
                    return
            except Exception:
                pass

        from sklearn.feature_extraction.text import TfidfVectorizer

        self._weighted_matrix = None
        self._feature_fields = [f for f in FIELD_WEIGHTS if any(a.get(f, "") for a in self.attractions)]

        matrices = []
        self._vectorizers = {}

        for field in self._feature_fields:
            docs = []
            for a in self.attractions:
                text = self._build_field_text(a, field)
                docs.append(self._tokenize(text))

            vec = TfidfVectorizer(
                analyzer="word" if field in ("description", "food", "culture",
                                             "basic_info", "travel_guide", "tips") else "char",
                ngram_range=(1, 2) if field in ("name", "province", "city", "category") else (2, 4),
                max_features=5000,
                sublinear_tf=True,
                min_df=1,
            )
            matrix = vec.fit_transform(docs)
            self._vectorizers[field] = vec
            matrices.append(matrix * FIELD_WEIGHTS[field])

        self._weighted_matrix = sparse.hstack(matrices) if len(matrices) > 1 else matrices[0]

        # 缓存到磁盘
        try:
            with open(cache_path, "wb") as f:
                pickle.dump({
                    "version": 2,
                    "count": len(self.attractions),
                    "matrix": self._weighted_matrix,
                    "vectorizers": self._vectorizers,
                    "fields": self._feature_fields,
                }, f)
        except Exception:
            pass

        self._use_semantic = False

    def search(
            self,
            query: str,
            top_k: int = 5,
            province: Optional[str] = None,
            category: Optional[str] = None,
            min_rating: Optional[float] = None,
    ) -> list:
        """加权检索"""
        cached = self._cached_search(query)
        results = cached[:top_k * 4]

        filtered = []
        for att, score in results:
            if province and att["province"] != province:
                continue
            if category and att["category"] != category:
                continue
            if min_rating and att.get("rating", 0) < min_rating:
                continue
            filtered.append((att, score))
            if len(filtered) >= top_k:
                break

        return filtered[:top_k]

    @lru_cache(maxsize=64)
    def _cached_search(self, query: str) -> list:
        """缓存检索结果"""
        from sklearn.metrics.pairwise import cosine_similarity

        query_vecs = []
        for field in self._feature_fields:
            vec = self._vectorizers.get(field)
            if vec is None:
                continue
            qv = vec.transform([self._tokenize(query)])
            query_vecs.append(qv * FIELD_WEIGHTS[field])

        from scipy import sparse
        full_query = sparse.hstack(query_vecs)
        scores = cosine_similarity(full_query, self._weighted_matrix).flatten()

        top_indices = scores.argsort()[-50:][::-1]
        return [
            (self.attractions[i], float(scores[i]))
            for i in top_indices
            if scores[i] > 0.001
        ]

    # ---- 语义检索（可选） ----
    def _try_build_semantic(self) -> bool:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            return False

        # 语义模型路径 (优先用 ModelScope 缓存)
        ms_cache = os.path.join(os.path.expanduser("~"),
                                ".cache/modelscope/hub/models")
        model_paths = [
            os.path.join(ms_cache, "BAAI/bge-small-zh-v1___5"),  # ModelScope
            os.path.join(ms_cache, "BAAI/bge-small-zh-v1.5"),   # 备选路径
            os.path.join(ms_cache, "iic/nlp_corom_sentence-embedding_chinese-base"),
            "shibing624/text2vec-base-chinese",                   # HuggingFace 直连
        ]

        for model_path in model_paths:
            try:
                self._embedder = SentenceTransformer(model_path, device="cpu")
                texts = [f"{a['name']}。{a.get('description','')}" for a in self.attractions]
                cache_path = os.path.join(CACHE_DIR, "semantic_emb.npy")
                if os.path.exists(cache_path):
                    embeddings = np.load(cache_path)
                else:
                    embeddings = self._embedder.encode(texts, show_progress_bar=True)
                    np.save(cache_path, embeddings)
                self._semantic_embeddings = np.array(embeddings).astype("float32")
                self._semantic_embeddings /= np.linalg.norm(self._semantic_embeddings, axis=1, keepdims=True)
                self._semantic_embedder = self._embedder
                return True
            except Exception:
                continue

        return False

    def _semantic_search(self, query: str, top_k: int) -> list:
        emb = self._semantic_embedder.encode([query])
        emb = np.array(emb).astype("float32")
        emb /= np.linalg.norm(emb)
        scores = self._semantic_embeddings @ emb.T
        scores = scores.flatten()
        top_indices = scores.argsort()[-top_k:][::-1]
        return [(self.attractions[i], float(scores[i]))
                for i in top_indices if 0 <= i < len(self.attractions)]

    # ---- 辅助方法 ----
    def hybrid_search(self, query: str, top_k: int = 5, **filters) -> list:
        """混合检索：TF-IDF + 语义融合 (RRF)"""
        tfidf_results = self.search(query, top_k=top_k * 3, **filters)
        sem_results = []
        if hasattr(self, "_semantic_index"):
            sem_results = self._semantic_search(query, top_k * 3)

        # RRF 融合
        scores = {}
        for i, (att, s) in enumerate(tfidf_results):
            scores[att["id"]] = scores.get(att["id"], 0) + 1.0 / (i + 60)
        for i, (att, s) in enumerate(sem_results):
            scores[att["id"]] = scores.get(att["id"], 0) + 1.0 / (i + 60)

        ranked = sorted(
            [(self.get_by_id(aid), sc) for aid, sc in scores.items()],
            key=lambda x: -x[1],
        )
        return ranked[:top_k]

    def get_by_id(self, aid: int):
        return self._id_index.get(aid)

    def get_by_province(self, province: str) -> list:
        return self._province_index.get(province, [])

    def get_by_category(self, category: str) -> list:
        return self._category_index.get(category, [])

    def fuzzy_search(self, query: str, top_k: int = 5) -> list:
        """拼音纠错 + 模糊匹配检索（含省份/城市拼音）"""
        # 尝试直接匹配名称
        query_lower = query.lower().replace(" ", "")
        exact_matches = [a for name, a in self._name_index.items()
                         if query_lower in name.lower()]
        if exact_matches:
            return [(a, 1.0) for a in exact_matches[:top_k]]

        # 拼音模糊匹配 (需安装 pypinyin)
        try:
            from pypinyin import pinyin, Style
            query_py = "".join([item[0] for item in pinyin(query, style=Style.NORMAL)]).replace(" ", "").lower()
            scored = []
            for a in self.attractions:
                name_py = "".join([item[0] for item in pinyin(a["name"], style=Style.NORMAL)]).replace(" ", "").lower()
                prov_py = "".join([item[0] for item in pinyin(a["province"], style=Style.NORMAL)]).replace(" ", "").lower()
                city_py = ""
                if a.get("city"):
                    city_py = "".join([item[0] for item in pinyin(a["city"], style=Style.NORMAL)]).replace(" ", "").lower()

                # 匹配名称、省份或城市拼音
                hit = False
                if query_py in name_py or name_py in query_py:
                    hit = True
                if query_py in prov_py or prov_py in query_py:
                    hit = True
                if city_py and (query_py in city_py or city_py in query_py):
                    hit = True
                # 拼音首字母匹配
                name_initials = "".join([item[0][0] for item in pinyin(a["name"], style=Style.NORMAL)])
                if query_py in name_initials:
                    hit = True

                if hit:
                    common_len = len(set(query_py) & set(name_py + prov_py + city_py))
                    score = common_len / max(len(query_py), 1)
                    if score > 0.3:
                        scored.append((score, a))

            scored.sort(key=lambda x: -x[0])
            if scored:
                return [(a, s) for s, a in scored[:top_k]]
        except ImportError:
            pass

        return []

    def get_provinces(self) -> list:
        return sorted(set(a["province"] for a in self.attractions))

    def get_categories(self) -> list:
        return sorted(set(a["category"] for a in self.attractions))

    def random_attractions(self, n: int = 5) -> list:
        import random
        return random.sample(self.attractions, min(n, len(self.attractions)))

    def get_stats(self) -> dict:
        return {
            "total": len(self.attractions),
            "provinces": len(self.get_provinces()),
            "categories": self.get_categories(),
        }

    def get_related(self, att: dict, top_n: int = 4) -> list:
        """获取关联景点（同省份 + 同类别的其他景点）"""
        same_province = [a for a in self.attractions
                         if a["province"] == att["province"] and a["id"] != att["id"]]
        same_category = [a for a in self.attractions
                         if a["category"] == att["category"] and a["id"] != att["id"]
                         and a not in same_province]

        related = (same_province[:3] + same_category[:3])[:top_n]
        return related
