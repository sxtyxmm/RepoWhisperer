import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Optional, Dict, Any
import gc
import psutil
import warnings

# Optional quantization imports
try:
    from transformers import BitsAndBytesConfig
    QUANTIZATION_AVAILABLE = True
except ImportError:
    BitsAndBytesConfig = None
    QUANTIZATION_AVAILABLE = False

try:
    import bitsandbytes
    BITSANDBYTES_AVAILABLE = True
except ImportError:
    BITSANDBYTES_AVAILABLE = False

warnings.filterwarnings("ignore", category=UserWarning)


class ModelInference:
    """Handles loading and inference with DeepSeek-Coder model."""
    
    def __init__(self, model_name: str, device: str = "auto", 
                 quantization: str = "4bit", max_tokens: int = 4096,
                 temperature: float = 0.1, top_p: float = 0.95):
        self.model_name = model_name
        self.device = device
        self.quantization = quantization
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        self.tokenizer = None
        self.model = None
        self.is_loaded = False
        
        print(f"Initializing model inference for {model_name}")
        print(f"Quantization: {quantization}, Device: {device}")
    
    def load_model(self) -> bool:
        """Load the model and tokenizer."""
        try:
            print("Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                padding_side="left"
            )
            
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            print("Loading model...")
            model_kwargs = {
                "trust_remote_code": True,
                "torch_dtype": torch.float16,
                "device_map": self.device if self.device != "auto" else "auto",
            }
            
            # Configure quantization
            if self.quantization == "4bit" and QUANTIZATION_AVAILABLE and BITSANDBYTES_AVAILABLE:
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                model_kwargs["quantization_config"] = quantization_config
                print("Using 4-bit quantization")
            elif self.quantization == "8bit" and QUANTIZATION_AVAILABLE and BITSANDBYTES_AVAILABLE:
                quantization_config = BitsAndBytesConfig(load_in_8bit=True)
                model_kwargs["quantization_config"] = quantization_config
                print("Using 8-bit quantization")
            elif self.quantization != "none":
                print(f"⚠️  Quantization libraries not available, falling back to full precision")
                print("💡 To enable quantization, install: pip install bitsandbytes")
            
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                **model_kwargs
            )
            
            self.is_loaded = True
            print("Model loaded successfully!")
            print(f"Model device: {next(self.model.parameters()).device}")
            print(f"Available GPU memory: {self._get_gpu_memory()}")
            
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("Attempting to load with CPU fallback...")
            
            try:
                # Fallback to CPU with lower precision
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    low_cpu_mem_usage=True
                )
                self.is_loaded = True
                print("Model loaded on CPU successfully!")
                return True
                
            except Exception as e2:
                print(f"Failed to load model even on CPU: {e2}")
                return False
    
    def generate_response(self, prompt: str, max_new_tokens: Optional[int] = None) -> str:
        """Generate response from the model."""
        if not self.is_loaded:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        max_new_tokens = max_new_tokens or min(self.max_tokens, 2048)
        
        try:
            # Prepare the prompt with proper formatting
            formatted_prompt = self._format_prompt(prompt)
            
            # Tokenize input
            inputs = self.tokenizer(
                formatted_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=4096,  # Leave room for generation
                padding=True
            )
            
            # Move to device
            if torch.cuda.is_available() and "cuda" in str(next(self.model.parameters()).device):
                inputs = {k: v.cuda() for k, v in inputs.items()}
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=max_new_tokens,
                    temperature=self.temperature,
                    top_p=self.top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1,
                    length_penalty=1.0,
                    no_repeat_ngram_size=3
                )
            
            # Decode response
            generated_tokens = outputs[0][inputs['input_ids'].shape[1]:]
            response = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)
            
            # Clean up the response
            response = self._clean_response(response)
            
            return response
            
        except torch.cuda.OutOfMemoryError:
            print("GPU out of memory. Trying with smaller max_new_tokens...")
            gc.collect()
            torch.cuda.empty_cache()
            
            # Retry with smaller generation length
            return self.generate_response(prompt, max_new_tokens // 2)
            
        except Exception as e:
            print(f"Error during generation: {e}")
            return f"Error generating response: {str(e)}"
    
    def _format_prompt(self, prompt: str) -> str:
        """Format the prompt for DeepSeek-Coder."""
        # DeepSeek-Coder instruction format
        formatted_prompt = f"""<｜begin▁of▁sentence｜>You are an AI programming assistant, utilizing the Deepseek Coder model, developed by Deepseek Company, and you only answer questions related to computer science. For politically sensitive questions, security and privacy issues, and other non-computer science questions, you will refuse to answer.

### Instruction:
{prompt}

### Response:
"""
        return formatted_prompt
    
    def _clean_response(self, response: str) -> str:
        """Clean up the generated response."""
        # Remove any remaining special tokens or artifacts
        response = response.strip()
        
        # Remove common artifacts
        artifacts = [
            "<｜end▁of▁sentence｜>",
            "<｜EOT｜>",
            "### Instruction:",
            "### Response:",
            "<|im_start|>",
            "<|im_end|>",
        ]
        
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        # Clean up any duplicate whitespace
        import re
        response = re.sub(r'\n\s*\n\s*\n', '\n\n', response)
        response = re.sub(r'[ \t]+', ' ', response)
        
        return response.strip()
    
    def generate_in_chunks(self, prompts: List[str]) -> List[str]:
        """Generate responses for multiple prompt chunks."""
        responses = []
        
        for i, prompt in enumerate(prompts):
            print(f"Processing chunk {i + 1}/{len(prompts)}...")
            
            try:
                response = self.generate_response(prompt)
                responses.append(response)
                
                # Cleanup between generations
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                
            except Exception as e:
                print(f"Error processing chunk {i + 1}: {e}")
                responses.append(f"Error processing chunk: {str(e)}")
        
        return responses
    
    def _get_gpu_memory(self) -> str:
        """Get GPU memory information."""
        if torch.cuda.is_available():
            device = torch.cuda.current_device()
            total = torch.cuda.get_device_properties(device).total_memory
            allocated = torch.cuda.memory_allocated(device)
            free = total - allocated
            
            return f"GPU {device}: {allocated/1e9:.1f}GB / {total/1e9:.1f}GB used, {free/1e9:.1f}GB free"
        else:
            ram = psutil.virtual_memory()
            return f"RAM: {ram.used/1e9:.1f}GB / {ram.total/1e9:.1f}GB used, {ram.available/1e9:.1f}GB available"
    
    def unload_model(self):
        """Unload the model to free memory."""
        if self.model:
            del self.model
        if self.tokenizer:
            del self.tokenizer
        
        self.model = None
        self.tokenizer = None
        self.is_loaded = False
        
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        print("Model unloaded successfully.")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model."""
        if not self.is_loaded:
            return {"status": "not_loaded"}
        
        info = {
            "status": "loaded",
            "model_name": self.model_name,
            "device": str(next(self.model.parameters()).device) if self.model else "unknown",
            "quantization": self.quantization,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "memory_info": self._get_gpu_memory()
        }
        
        if hasattr(self.model, 'config'):
            info["model_config"] = {
                "vocab_size": getattr(self.model.config, 'vocab_size', 'unknown'),
                "hidden_size": getattr(self.model.config, 'hidden_size', 'unknown'),
                "num_attention_heads": getattr(self.model.config, 'num_attention_heads', 'unknown'),
                "num_hidden_layers": getattr(self.model.config, 'num_hidden_layers', 'unknown'),
            }
        
        return info


class LocalInferenceWrapper:
    """Wrapper for easy model management."""
    
    def __init__(self, config: Dict[str, Any]):
        model_config = config.get('model', {})
        
        self.inference = ModelInference(
            model_name=model_config.get('name', 'deepseek-ai/deepseek-coder-33b-instruct'),
            device=model_config.get('device', 'auto'),
            quantization=model_config.get('quantization', '4bit'),
            max_tokens=model_config.get('max_tokens', 4096),
            temperature=model_config.get('temperature', 0.1),
            top_p=model_config.get('top_p', 0.95)
        )
    
    def __enter__(self):
        """Context manager entry."""
        success = self.inference.load_model()
        if not success:
            raise RuntimeError("Failed to load model")
        return self.inference
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.inference.unload_model()
