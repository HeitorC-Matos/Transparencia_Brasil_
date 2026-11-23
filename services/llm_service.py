"""Inferência com Qwen instalado em disco local; nunca consulta serviços remotos.

Torch/Transformers são importados somente durante o carregamento. Assim, endpoints
legados e testes podem funcionar mesmo em computadores sem GPU ou pesos do modelo.
"""
from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Literal

MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "qwen3-4b-instruct-2507"


class ModeloIndisponivel(RuntimeError):
    """Modelo ausente ou ambiente local sem condições para inferência."""


class ModeloOcupado(RuntimeError):
    """Outra geração já está usando a GPU local."""


class TempoLimiteGeracao(TimeoutError):
    """A geração atingiu o limite de processamento configurado."""


class MemoriaInsuficiente(ModeloIndisponivel):
    """A GPU não possui VRAM suficiente para esta requisição."""


class TextoMuitoLongo(ValueError):
    """Prompt excede o limite de tokens definido para a GPU."""


@dataclass(frozen=True)
class ResultadoGeracao:
    texto: str
    tokens_entrada: int
    tokens_saida: int
    tempo_ms: int


class ServicoLLM:
    """Gerencia uma instância local, com carregamento e inferência serializados.

    O modelo é carregado somente após o primeiro POST. Não se instala ou baixa
    nenhum peso no startup da API, e a API nunca chama o Hugging Face Hub.
    """

    def __init__(self, caminho: Path | None = None):
        valor = os.getenv("TP4_MODEL_DIR")
        self.caminho = Path(valor).expanduser().resolve() if valor else (caminho or DEFAULT_MODEL_PATH)
        self._tokenizer = None
        self._model = None
        self._torch = None
        self._last_error: str | None = None
        self._load_lock = threading.Lock()
        self._generation_lock = threading.Lock()
        self._max_input_tokens = 2048
        # Valor seguro frente ao timeout HTTP de 300 s utilizado pelo Streamlit.
        try:
            tempo = int(os.getenv("TP4_LLM_MAX_SECONDS", "180"))
        except ValueError:
            tempo = 180
        self._max_generation_seconds = max(30, min(240, tempo))

    def status(self) -> dict:
        if self._model is not None:
            situacao = "carregado"
        elif not self._arquivos_presentes():
            situacao = "arquivos_ausentes"
        elif self._last_error:
            situacao = "erro_carregamento"
        else:
            situacao = "nao_carregado"
        return {
            "status": situacao,
            "modelo": MODEL_ID,
            "execucao_local": True,
            "caminho_modelo": str(self.caminho),
            "detalhe": ("Faça download com 'python scripts/baixar_modelo.py'" if situacao == "arquivos_ausentes"
                        else "Modelo pronto para processamento" if situacao == "carregado"
                        else "O modelo será carregado na primeira solicitação" if situacao == "nao_carregado"
                        else "Verifique os logs locais e as dependências CUDA"),
        }

    def _arquivos_presentes(self) -> bool:
        return ((self.caminho / "config.json").is_file()
                and (self.caminho / "tokenizer_config.json").is_file()
                and any(self.caminho.glob("*.safetensors")))

    def carregar(self) -> None:
        if self._model is not None:
            return
        with self._load_lock:
            if self._model is not None:
                return
            if not self._arquivos_presentes():
                raise ModeloIndisponivel(
                    "Os pesos do modelo não estão disponíveis na pasta local. "
                    "Execute 'python scripts/baixar_modelo.py' quando houver internet."
                )
            # Proíbe acesso à rede mesmo quando a variável não foi configurada pelo usuário.
            os.environ["HF_HUB_OFFLINE"] = "1"
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
            except ImportError as erro:
                self._last_error = type(erro).__name__
                raise ModeloIndisponivel(
                    "Dependências do Qwen não instaladas. Instale requirements-llm.txt "
                    "e uma versão PyTorch com CUDA."
                ) from erro
            if not torch.cuda.is_available():
                self._last_error = "CUDA indisponível"
                raise ModeloIndisponivel(
                    "GPU CUDA não disponível. Verifique o driver NVIDIA e a instalação "
                    "do PyTorch com suporte a CUDA."
                )
            try:
                tokenizer = AutoTokenizer.from_pretrained(
                    str(self.caminho), local_files_only=True, trust_remote_code=False
                )
                quantizacao = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                modelo = AutoModelForCausalLM.from_pretrained(
                    str(self.caminho),
                    local_files_only=True,
                    trust_remote_code=False,
                    quantization_config=quantizacao,
                    device_map={"": 0},
                    dtype=torch.float16,
                    low_cpu_mem_usage=True,
                )
                modelo.eval()
            except (RuntimeError, ValueError, OSError, ImportError) as erro:
                self._last_error = type(erro).__name__
                if "out of memory" in str(erro).lower():
                    raise MemoriaInsuficiente(
                        "A memória da GPU é insuficiente para carregar o modelo. "
                        "Feche outros programas que usam a placa e reinicie a API."
                    ) from erro
                raise ModeloIndisponivel(
                    "O Qwen não pôde ser carregado na GPU. Verifique a memória de vídeo "
                    "disponível, a integridade dos pesos e as dependências locais."
                ) from erro
            self._torch = torch
            self._tokenizer = tokenizer
            self._model = modelo
            self._last_error = None

    def gerar(self, texto: str, operacao: Literal["resumo", "explicacao"],
              max_novos_tokens: int = 384, *,
              instrucoes_sistema: str | None = None,
              instrucao_tarefa: str | None = None) -> ResultadoGeracao:
        # A trava cobre inclusive o carregamento, impedindo carregamentos concorrentes.
        if not self._generation_lock.acquire(blocking=False):
            raise ModeloOcupado("O modelo está processando outra solicitação. Tente novamente.")
        try:
            inicio = perf_counter()
            self.carregar()
            assert self._model is not None and self._tokenizer is not None
            orientacao = (
                "Você é um assistente do Transparência Brasil. "
                "Responda em português brasileiro. Seja objetivo e fiel ao conteúdo recebido. "
                "Não invente fatos, fontes, números ou conclusões que não apareçam no texto. "
                "Diferencie dados ilustrativos de dados oficiais declarados ao Siconfi. "
                "Os dados do Siconfi não foram auditados por este sistema. "
                "Não misture bases, não invente valores e não infira causalidade sem evidência."
            )
            tarefa = (
                "Resuma o texto a seguir, preservando as ideias centrais e as ressalvas:\n\n"
                if operacao == "resumo" else
                "Explique de forma clara o texto a seguir, sem acrescentar informações não verificadas:\n\n"
            )
            mensagens = [
                {"role": "system", "content": instrucoes_sistema if instrucoes_sistema is not None else orientacao},
                {"role": "user", "content": (instrucao_tarefa + "\n\n" + texto) if instrucao_tarefa is not None else tarefa + texto},
            ]
            prompt = self._tokenizer.apply_chat_template(
                mensagens, tokenize=False, add_generation_prompt=True
            )
            entradas = self._tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
            qtd_entrada = int(entradas["input_ids"].shape[-1])
            if qtd_entrada > self._max_input_tokens:
                raise TextoMuitoLongo(
                    "O texto excede o limite de 2.048 tokens de entrada para esta configuração. "
                    "Divida-o em trechos menores."
                )
            entradas = entradas.to(self._model.device)
            # max_time faz a geração parar cooperativamente entre tokens; não
            # encerra à força um kernel CUDA que já está em execução.
            try:
                with self._torch.inference_mode():
                    saidas = self._model.generate(
                        **entradas,
                        max_new_tokens=max_novos_tokens,
                        max_time=self._max_generation_seconds,
                        do_sample=False,
                        use_cache=True,
                        pad_token_id=self._tokenizer.eos_token_id,
                    )
            except RuntimeError as erro:
                if "out of memory" in str(erro).lower():
                    try:
                        self._torch.cuda.empty_cache()
                    except Exception:
                        pass
                    raise MemoriaInsuficiente(
                        "A memória de vídeo ficou insuficiente durante a geração. "
                        "Reduza o tamanho do texto ou feche aplicativos que usam a GPU."
                    ) from erro
                raise
            if perf_counter() - inicio >= self._max_generation_seconds:
                raise TempoLimiteGeracao(
                    "A geração ultrapassou o tempo máximo configurado. "
                    "Envie um texto menor ou reduza o limite de tokens."
                )
            ids_gerados = saidas[0][qtd_entrada:]
            resposta = self._tokenizer.decode(ids_gerados, skip_special_tokens=True).strip()
            if not resposta:
                raise RuntimeError("O modelo terminou sem gerar uma resposta textual.")
            return ResultadoGeracao(
                texto=resposta,
                tokens_entrada=qtd_entrada,
                tokens_saida=int(len(ids_gerados)),
                tempo_ms=round((perf_counter() - inicio) * 1000),
            )
        finally:
            self._generation_lock.release()


servico_llm = ServicoLLM()
