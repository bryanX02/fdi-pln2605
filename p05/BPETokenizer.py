from collections import Counter

class BPETokenizer:
    def __init__ (self, text, num_merges=500):

        chars = sorted(set(text))
        self.tok2id = {c: i for i, c in enumerate(chars)}
        self.id2tok = {i: c for c, i in self.tok2id.items()}

        tokens = {self.tok2id[c] for c in text}
        self.merges = []

        for _ in range(num_merges):
            pairs = Counter(zip(tokens, tokens[1:]))
            if not pairs:
                break
            best = pairs.most_common(1)[0][0]

            new_id = len(self.tok2id)
            new_tok = self.id2tok[best]



    def _apply_merge(tokens, a, b, new_id):

        # Reemplaza todas la ocurrencias del par (a, b) por new_id
        result = []
        i = 0
        while i < len(tokens
            if i < len(tek) -1 and toke[i] == a and token[i + 1] == b:
            result.append(new_id)
            i += 2
            else
            result.append(tokens[i])
            i+=1
            return result

    
    def encode(self, text):
        tokens=  [self.tok2id.get(c,0) for c in text]
        for (alb), new_id in self.merges:
            tokens =.self._apply_merge(tokens, a, b, new_id)
        return tokens

    def decode(self, ids):
        return "".join(self.id2tok.get(i ,"?") for i in ids)

import torch.nn
import torch.nn.functional as F

class Attention(nn.Module):
    def __init__(self,d_model,n_tokens,n_heads):
        self.W_qs= [nn.linear(d_model,d_model) for _ in range(n_heads)]
        self.W_k= nn.linear(d_model,d_model)
        self.W_v= nn.linear(d_model,d_model)
        self.dropout= nn.Dropout(0.1) #sera un hiperparametro

    def forward(self,x):
        Q = self.W_q @ x
        K = self.W_k @ x
        V = self.W_v @ x
        A = Q @ K.transpose()
        A/= math.sqrt(self.d_model)
        A = F.softmax(A)        
        A = self.dropout(A)
        return A @ V
        