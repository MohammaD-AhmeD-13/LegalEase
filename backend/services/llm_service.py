import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

def _lazy_imports():
	try:
		import torch
		from transformers import AutoModelForCausalLM, AutoTokenizer
		try:
			from transformers import BitsAndBytesConfig
		except ImportError:  # pragma: no cover
			BitsAndBytesConfig = None
		return torch, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
	except Exception as exc:  # pragma: no cover
		raise RuntimeError(
			"LLM dependencies are not available. Install torch/transformers or set LLM_ENABLED=0."
		) from exc

try:
	import bitsandbytes as _bnb  # noqa: F401
	_BNB_AVAILABLE = True
except Exception:  # pragma: no cover
	_BNB_AVAILABLE = False

_LLM_ENABLED = os.getenv("LLM_ENABLED", "1") == "1"
_LLM_THREAD_POOL = ThreadPoolExecutor(max_workers=2)


class LLMService:
	def __init__(
		self,
		model_id: str = "Qwen/Qwen2.5-1.5B-Instruct",
		device_map: Optional[str] = None,
	) -> None:
		torch, AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig = _lazy_imports()
		self._torch = torch
		self.model_id = model_id
		self.device_map = device_map or os.getenv("LLM_DEVICE_MAP", "cpu")
		self.use_4bit = os.getenv("LLM_4BIT", "0") == "1"
		self.tokenizer = AutoTokenizer.from_pretrained(
			self.model_id,
			use_fast=True,
			trust_remote_code=True,
		)
		if self.tokenizer.pad_token_id is None:
			self.tokenizer.pad_token = self.tokenizer.eos_token

		quantization_config = None
		if (
			self.use_4bit
			and torch.cuda.is_available()
			and BitsAndBytesConfig is not None
			and _BNB_AVAILABLE
		):
			quantization_config = BitsAndBytesConfig(
				load_in_4bit=True,
				bnb_4bit_compute_dtype=torch.float16,
				bnb_4bit_use_double_quant=True,
				bnb_4bit_quant_type="nf4",
			)
		elif self.use_4bit and not _BNB_AVAILABLE:
			self.use_4bit = False
		self.model = AutoModelForCausalLM.from_pretrained(
			self.model_id,
			torch_dtype="auto",
			device_map=self.device_map,
			trust_remote_code=True,
			quantization_config=quantization_config,
		)
		self.model.eval()

	def generate_sync(self, prompt: str, max_new_tokens: int = 256) -> str:
		torch = self._torch
		messages = [
			{
				"role": "system",
				"content": "You are LegalEase, a legal assistant for Pakistan. Follow the user's language instruction exactly.",
			},
			{"role": "user", "content": prompt},
		]
		with torch.inference_mode():
			input_ids = self.tokenizer.apply_chat_template(
				messages,
				add_generation_prompt=True,
				return_tensors="pt",
			)
			input_ids = input_ids.to(self.model.device)
			attention_mask = input_ids.ne(self.tokenizer.pad_token_id)

			output_ids = self.model.generate(
				input_ids,
				attention_mask=attention_mask,
				max_new_tokens=max_new_tokens,
				do_sample=False,
				pad_token_id=self.tokenizer.pad_token_id,
			)
			output_text = self.tokenizer.decode(
				output_ids[0][input_ids.shape[-1]:],
				skip_special_tokens=True,
			)
		return output_text.strip()

	async def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
		loop = asyncio.get_running_loop()
		return await loop.run_in_executor(
			_LLM_THREAD_POOL,
			self.generate_sync,
			prompt,
			max_new_tokens,
		)


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
	if not _LLM_ENABLED:
		raise RuntimeError("LLM is disabled via LLM_ENABLED=0")
	global _llm_service
	if _llm_service is None:
		_llm_service = LLMService()
	return _llm_service


def is_llm_ready() -> bool:
	return _llm_service is not None


def is_llm_enabled() -> bool:
	return _LLM_ENABLED


def get_llm_info() -> dict:
	if not _LLM_ENABLED:
		return {"status": "disabled"}
	if _llm_service is None:
		return {"status": "loading"}

	device = str(_llm_service.model.device)
	return {
		"status": "loaded",
		"model_id": _llm_service.model_id,
		"device": device,
		"device_map": _llm_service.device_map,
		"use_4bit": _llm_service.use_4bit,
	}
