import copy
import logging
import math
import os
import re
import string

import datrie
from hanziconv import HanziConv
from nltk import word_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer


class RagTokenizer:
    def key_(self, line):
        return str(line.lower().encode("utf-8"))[2:-1]

    def rkey_(self, line):
        return str(("DD" + (line[::-1].lower())).encode("utf-8"))[2:-1]

    def loadDict_(self, fnm):
        print(f"[HUQIE]:Build trie from {fnm}")
        try:
            of = open(fnm, "r", encoding="utf-8")
            while True:
                line = of.readline()
                if not line:
                    break
                line = re.sub(r"[\r\n]+", "", line)
                line = re.split(r"[ \t]", line)
                k = self.key_(line[0])
                F = int(math.log(float(line[1]) / self.DENOMINATOR) + 0.5)
                if k not in self.trie_ or self.trie_[k][0] < F:
                    self.trie_[self.key_(line[0])] = (F, line[2])
                self.trie_[self.rkey_(line[0])] = 1

            dict_file_cache = fnm + ".trie"
            print(f"[HUQIE]:Build trie cache to {dict_file_cache}")
            self.trie_.save(dict_file_cache)
            of.close()
        except Exception:
            logging.exception(f"[HUQIE]:Build trie {fnm} failed")

    def __init__(self):
        self.DENOMINATOR = 1000000
        self.DIR_ = os.path.join(os.path.dirname(os.path.realpath(__file__)), "res", "huqie")

        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()

        self.SPLIT_CHAR = r"([ ,\.<>/?;:'\[\]\\`!@#$%^&*\(\)\{\}\|_+=《》，。？、；‘’：“”【】~！￥%……（）——-]+|[a-zA-Z0-9,\.-]+)"

        trie_file_name = self.DIR_ + ".txt.trie"
        txt_file_name = self.DIR_ + ".txt"
        
        if os.path.exists(txt_file_name):
            try:
                self.trie_ = datrie.Trie(string.printable)
                self.loadDict_(txt_file_name)
                return
            except Exception:
                logging.warning(f"[HUQIE]:Build trie from txt failed, using default")
        
        if os.path.exists(trie_file_name):
            try:
                self.trie_ = datrie.Trie.load(trie_file_name)
                return
            except Exception:
                logging.warning(f"[HUQIE]:Fail to load trie file {trie_file_name}")
        
        self.trie_ = datrie.Trie(string.printable)

    def _strQ2B(self, ustring):
        rstring = ""
        for uchar in ustring:
            inside_code = ord(uchar)
            if inside_code == 0x3000:
                inside_code = 0x0020
            else:
                inside_code -= 0xFEE0
            if inside_code < 0x0020 or inside_code > 0x7E:
                rstring += uchar
            else:
                rstring += chr(inside_code)
        return rstring

    def _tradi2simp(self, line):
        return HanziConv.toSimplified(line)

    def dfs_(self, chars, s, preTks, tkslist):
        res = s
        if s >= len(chars):
            tkslist.append(preTks)
            return res

        S = s + 1
        if s + 2 <= len(chars):
            t1, t2 = "".join(chars[s : s + 1]), "".join(chars[s : s + 2])
            if self.trie_.has_keys_with_prefix(self.key_(t1)) and not self.trie_.has_keys_with_prefix(self.key_(t2)):
                S = s + 2
        if len(preTks) > 2 and len(preTks[-1][0]) == 1 and len(preTks[-2][0]) == 1 and len(preTks[-3][0]) == 1:
            t1 = preTks[-1][0] + "".join(chars[s : s + 1])
            if self.trie_.has_keys_with_prefix(self.key_(t1)):
                S = s + 2

        for e in range(S, len(chars) + 1):
            t = "".join(chars[s:e])
            k = self.key_(t)

            if e > s + 1 and not self.trie_.has_keys_with_prefix(k):
                break

            if k in self.trie_:
                pretks = copy.deepcopy(preTks)
                if k in self.trie_:
                    pretks.append((t, self.trie_[k]))
                else:
                    pretks.append((t, (-12, "")))
                res = max(res, self.dfs_(chars, e, pretks, tkslist))

        if res > s:
            return res

        t = "".join(chars[s : s + 1])
        k = self.key_(t)
        if k in self.trie_:
            preTks.append((t, self.trie_[k]))
        else:
            preTks.append((t, (-12, "")))

        return self.dfs_(chars, s + 1, preTks, tkslist)

    def freq(self, tk):
        k = self.key_(tk)
        if k not in self.trie_:
            return 0
        return int(math.exp(self.trie_[k][0]) * self.DENOMINATOR + 0.5)

    def score_(self, tfts):
        B = 30
        F, L, tks = 0, 0, []
        for tk, (freq, tag) in tfts:
            F += freq
            L += 0 if len(tk) < 2 else 1
            tks.append(tk)
        L /= len(tks)
        logging.debug("[SC] {} {} {} {} {}".format(tks, len(tks), L, F, B / len(tks) + L + F))
        return tks, B / len(tks) + L + F

    def sortTks_(self, tkslist):
        res = []
        for tfts in tkslist:
            tks, s = self.score_(tfts)
            res.append((tks, s))
        return sorted(res, key=lambda x: x[1], reverse=True)

    def merge_(self, tks):
        res = []
        tks = re.sub(r"[ ]+", " ", tks).split()
        s = 0
        while True:
            if s >= len(tks):
                break
            E = s + 1
            for e in range(s + 2, min(len(tks) + 2, s + 6)):
                tk = "".join(tks[s:e])
                if re.search(self.SPLIT_CHAR, tk) and self.freq(tk):
                    E = e
            res.append("".join(tks[s:E]))
            s = E

        return " ".join(res)

    def maxForward_(self, line):
        res = []
        s = 0
        while s < len(line):
            e = s + 1
            t = line[s:e]
            while e < len(line) and self.trie_.has_keys_with_prefix(self.key_(t)):
                e += 1
                t = line[s:e]

            while e - 1 > s and self.key_(t) not in self.trie_:
                e -= 1
                t = line[s:e]

            if self.key_(t) in self.trie_:
                res.append((t, self.trie_[self.key_(t)]))
            else:
                res.append((t, (0, "")))

            s = e

        return self.score_(res)

    def maxBackward_(self, line):
        res = []
        s = len(line) - 1
        while s >= 0:
            e = s + 1
            t = line[s:e]
            while s > 0 and self.trie_.has_keys_with_prefix(self.rkey_(t)):
                s -= 1
                t = line[s:e]

            while s + 1 < e and self.key_(t) not in self.trie_:
                s += 1
                t = line[s:e]

            if self.key_(t) in self.trie_:
                res.append((t, self.trie_[self.key_(t)]))
            else:
                res.append((t, (0, "")))

            s -= 1

        return self.score_(res[::-1])

    def _split_by_lang(self, line):
        txt_lang_pairs = []
        arr = re.split(self.SPLIT_CHAR, line)
        for a in arr:
            if not a:
                continue
            s = 0
            e = s + 1
            zh = is_chinese(a[s])
            while e < len(a):
                _zh = is_chinese(a[e])
                if _zh == zh:
                    e += 1
                    continue
                txt_lang_pairs.append((a[s:e], zh))
                s = e
                e = s + 1
                zh = _zh
            if s >= len(a):
                continue
            txt_lang_pairs.append((a[s:e], zh))
        return txt_lang_pairs

    def tokenize(self, line: str) -> str:
        line = re.sub(r"\W+", " ", line)
        line = self._strQ2B(line).lower()
        line = self._tradi2simp(line)

        arr = self._split_by_lang(line)
        res = []

        for L, lang in arr:
            if not lang:
                res.extend([self.stemmer.stem(self.lemmatizer.lemmatize(t)) for t in word_tokenize(L)])
                continue

            if len(L) < 2 or re.match(r"[a-z\.-]+$", L) or re.match(r"[0-9\.-]+$", L):
                res.append(L)
                continue

            tks, s = self.maxForward_(L)
            tks1, s1 = self.maxBackward_(L)

            i, j = 0, 0
            _i, _j = 0, 0

            same = 0
            while i + same < len(tks1) and j + same < len(tks) and tks1[i + same] == tks[j + same]:
                same += 1
            if same > 0:
                res.append(" ".join(tks[j : j + same]))

            _i = i + same
            _j = j + same
            j = _j + 1
            i = _i + 1

            while i < len(tks1) and j < len(tks):
                tk1, tk = "".join(tks1[_i:i]), "".join(tks[_j:j])

                if tk1 != tk:
                    if len(tk1) > len(tk):
                        j += 1
                    else:
                        i += 1
                    continue

                if tks1[i] != tks[j]:
                    i += 1
                    j += 1
                    continue

                tkslist = []
                self.dfs_("".join(tks[_j:j]), 0, [], tkslist)
                if tkslist:
                    res.append(" ".join(self.sortTks_(tkslist)[0][0]))

                same = 1
                while i + same < len(tks1) and j + same < len(tks) and tks1[i + same] == tks[j + same]:
                    same += 1
                res.append(" ".join(tks[j : j + same]))

                _i = i + same
                _j = j + same
                j = _j + 1
                i = _i + 1

            if _i < len(tks1):
                assert _j < len(tks)
                assert "".join(tks1[_i:]) == "".join(tks[_j:])
                tkslist = []
                self.dfs_("".join(tks[_j:]), 0, [], tkslist)
                if tkslist:
                    res.append(" ".join(self.sortTks_(tkslist)[0][0]))

        res_str = " ".join(res)
        return self.merge_(res_str)


def is_chinese(s):
    if s >= "\u4e00" and s <= "\u9fa5":
        return True
    else:
        return False

