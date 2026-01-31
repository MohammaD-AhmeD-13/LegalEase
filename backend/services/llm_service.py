import os
from typing import Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

try:
	from transformers import BitsAndBytesConfig
except ImportError:  # pragma: no cover
	BitsAndBytesConfig = None

try:
	import bitsandbytes as _bnb  # noqa: F401
	_BNB_AVAILABLE = True
except Exception:  # pragma: no cover
	_BNB_AVAILABLE = False


class LLMService:
	def __init__(
		self,
		model_id: str = "Qwen/Qwen2.5-3B-Instruct",
		device_map: Optional[str] = None,
	) -> None:
		self.model_id = model_id
		self.device_map = device_map or os.getenv("LLM_DEVICE_MAP", "auto")
		self.use_4bit = os.getenv("LLM_4BIT", "1") == "1"
		self.tokenizer = AutoTokenizer.from_pretrained(
			self.model_id,
			use_fast=True,
			trust_remote_code=True,
		)
		if self.tokenizer.pad_token_id is None:
			self.tokenizer.pad_token = self.tokenizer.eos_token

		quantization_config = None
		if self.use_4bit and BitsAndBytesConfig is not None and _BNB_AVAILABLE:
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

	@torch.inference_mode()
	def generate(self, prompt: str, max_new_tokens: int = 256) -> str:
		messages = [
			{"role": "system", "content": "You are LegalEase, a bilingual (Urdu + English) legal assistant for Pakistan."},
			{"role": "user", "content": prompt},
		]
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
			do_sample=True,
			temperature=0.2,
			top_p=0.9,
			pad_token_id=self.tokenizer.pad_token_id,
		)
		output_text = self.tokenizer.decode(
			output_ids[0][input_ids.shape[-1]:],
			skip_special_tokens=True,
		)
		return output_text.strip()


_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
	global _llm_service
	if _llm_service is None:
		_llm_service = LLMService()
	return _llm_service


def is_llm_ready() -> bool:
	return _llm_service is not None
