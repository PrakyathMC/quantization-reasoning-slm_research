from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import psutil
from datetime import datetime

log = []

def log_print(msg):
    print(msg)
    log.append(msg)

log_print(f"Timestamp: {datetime.now()}")
log_print(f"RAM before loading: {round(psutil.virtual_memory().used / 1e9, 2)} GB")

model_path = "../base_model_weights"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16,
    device_map="cpu"
)

log_print(f"RAM after loading: {round(psutil.virtual_memory().used / 1e9, 2)} GB")

inputs = tokenizer("The capital of France is", return_tensors="pt")
outputs = model.generate(**inputs, max_new_tokens=10)
result = tokenizer.decode(outputs[0])
log_print(f"Generated text: {result}")

# Save results
with open("load_test_results.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(log))

log_print("Results saved to load_test_results.txt")