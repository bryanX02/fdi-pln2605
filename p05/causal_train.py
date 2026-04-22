import time

import torch
from loguru import logger
from torch.utils.data import DataLoader, Dataset


class TextDataset(Dataset):
    """Ventana deslizante sobre un tensor de tokens para language modeling.

    Cada sample es un par (x, y) de longitud `seq_len`, donde y es x
    desplazado una posicion a la derecha (predecir el siguiente token).
    """

    def __init__(self, data, seq_len):
        self.data = data
        self.seq_len = seq_len

    def __len__(self):
        return len(self.data) - self.seq_len

    def __getitem__(self, idx):
        x = self.data[idx : idx + self.seq_len]
        y = self.data[idx + 1 : idx + self.seq_len + 1]
        return x, y


def _make_dataloaders(train_tokens, val_tokens, context_size, batch_size):
    """Los dataloaders se encargan de ir aportando pares para el entrenamiento,
    incluyendo batching, mezcla aleatoria, etc.

    Recibe tokens de entrenamiento y validación por separado, permitiendo
    combinar múltiples fuentes de datos con distintas políticas de split.
    """
    train_data = torch.tensor(train_tokens, dtype=torch.long)
    val_data = torch.tensor(val_tokens, dtype=torch.long)

    train_ds = TextDataset(train_data, context_size)
    val_ds = TextDataset(val_data, context_size)
    logger.info(f"Train: {len(train_ds):,} muestras, Val: {len(val_ds):,}")

    # Los dataloaders implementan utilidades para el entrenamiento de
    # modelos. Devolvemos uno para train y otro para val
    return (
        DataLoader(train_ds, batch_size=batch_size, shuffle=True,num_workers=6, pin_memory=True),
        DataLoader(val_ds, batch_size=batch_size, num_workers=6, pin_memory=True),
    )


def _run_epoch(model, dataloader, optimizer=None):
    """Ejecuta una epoch completa de entrenamiento o evaluación.

    Si se pasa optimizer, entrena el modelo (forward + backward + step).
    Si no, evalúa sin calcular gradientes.
    Devuelve la media de loss sobre todos los batches.
    """
    total_loss, n = 0, 0
    device = next(model.parameters()).device

    if optimizer:
        model.train()
        torch.set_grad_enabled(True)
    else:
        model.eval()
        torch.set_grad_enabled(False)

    for x, y in dataloader:
        x, y = x.to(device), y.to(device)

        if optimizer:
            optimizer.zero_grad()

        # Pase forward, creando el grafo computacional y calculando loss
        _, loss = model(x, y)

        if optimizer:
            # Propaga la pérdida hacia atrás siguiendo el grafo
            loss.backward()
            # Reducimos "gradientes explosivos" para evitar anomalías de train
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            # Hacemos un paso del optimizador (eg un pequeño paso de descenso
            # siguiendo el gradiente, o lo que determine el optimizador)
            optimizer.step()

        total_loss += loss.item()
        n += 1

    # Devolvemos la media de loss en este epoch
    return total_loss / n


def train(
    model,
    train_tokens,
    val_tokens,
    epochs=5,
    context_size=128,
    batch_size=256,
    lr=3e-4,
):
    """Entrena el modelo de lenguaje causal sobre los tokens dados.

    Recibe tokens de entrenamiento y validación por separado.
    Realiza `epochs` épocas de entrenamiento con AdamW, registrando train/val
    loss en cada época.
    """

    train_dl, val_dl = _make_dataloaders(train_tokens, val_tokens, context_size, batch_size)

    # El optimizador ajusta los parámetros que le pasamos en función del
    # gradiente (calculado con forward y backward) y la tasa de aprendizaje
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)

    t0 = time.time()
    for epoch in range(epochs):
        train_loss = _run_epoch(model, train_dl, optimizer)
        val_loss = _run_epoch(model, val_dl, None)
        elapsed = time.time() - t0
        logger.info(
            f"Epoca {epoch + 1}/{epochs} | train={train_loss:.4f} | "
            f"val={val_loss:.4f} | tiempo={elapsed:.1f}s"
        )

    elapsed = time.time() - t0
    logger.info(f"Entrenamiento finalizado en {elapsed:.1f}s")


if __name__ == "__main__":
    import glob
    import os

    from p05.causal_llm import CausalLLM
    from p05.tokenizer import BPETokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"

    VOCAB_SIZE = 600
    CONTEXT_SIZE = 200
    TRAIN_RATIO = 0.9

    # --- Cargar textos de alicia/ (train + validación) ---
    alicia_files = sorted(glob.glob(os.path.join("alicia", "*.txt")))
    alicia_text = ""
    for path in alicia_files:
        with open(path, encoding="utf-8") as f:
            alicia_text += f.read() + "\n"
    logger.info(f"alicia/: {len(alicia_files)} fichero(s), {len(alicia_text):,} caracteres")

    # --- Cargar textos de new txt/ (solo train) ---
    newtxt_files = sorted(glob.glob(os.path.join("new txt", "*.txt")))
    newtxt_text = ""
    for path in newtxt_files:
        with open(path, encoding="utf-8") as f:
            newtxt_text += f.read() + "\n"
    logger.info(f"new txt/: {len(newtxt_files)} fichero(s), {len(newtxt_text):,} caracteres")

    # Entrenamos el tokenizador sobre todo el texto disponible
    all_text = alicia_text + newtxt_text
    tokenizer = BPETokenizer(all_text, vocab_size=VOCAB_SIZE)

    # Tokens de alicia/ → split train/val
    alicia_tokens = tokenizer.encode(alicia_text)
    split = int(TRAIN_RATIO * len(alicia_tokens))
    alicia_train_tokens = alicia_tokens[:split]
    alicia_val_tokens = alicia_tokens[split:]

    # Tokens de new txt/ → solo train
    newtxt_train_tokens = tokenizer.encode(newtxt_text)[:300000]

    # Combinamos los tokens de entrenamiento
    train_tokens = alicia_train_tokens + newtxt_train_tokens
    val_tokens = alicia_val_tokens

    logger.info(
        f"Tokens — train: {len(train_tokens):,} "
        f"(alicia {len(alicia_train_tokens):,} + new txt {len(newtxt_train_tokens):,}), "
        f"val: {len(val_tokens):,} (alicia)"
    )

    model = CausalLLM(
        vocab_size=tokenizer.vocab_size,
        max_seq_len=CONTEXT_SIZE,
        d_model=200,
        n_heads=4,
        n_layers=6,=1
        expansion=4,
        dropout=0.1,
    ).to(device)

    train(model, train_tokens, val_tokens, epochs=5, context_size=CONTEXT_SIZE)
    torch.save(model.state_dict(), "model.pt")

    prompt = "alice and the cat were studying for the exam. what "
    pred = model.generate(tokenizer.encode(prompt), max_tokens=200)
    logger.opt(colors=True).info(f"<cyan>{prompt}</cyan>{tokenizer.decode(pred)[:500]}")