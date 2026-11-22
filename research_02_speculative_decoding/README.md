# Speculative Decoding Inference Study

## Research question

Under what target–draft model pairings and decoding configurations does speculative decoding reduce inference latency and increase generation throughput while preserving the target model's output quality in local LLM deployment?

## Initial scope

This study will compare standard decoding with draft-model speculative decoding using llama.cpp. Experiments will measure latency, generation throughput, draft-token acceptance rate, memory usage, model size, and output quality.

## Planned factors

- Target–draft model pairings
- Draft sequence length
- Model precision and quantization
- Standard versus speculative decoding

## Status

Project initialized. Experimental design and model selection are pending.
