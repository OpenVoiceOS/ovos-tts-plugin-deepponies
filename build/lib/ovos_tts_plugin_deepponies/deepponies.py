import json
import re
from os import makedirs
from os.path import dirname, isfile

import nltk
import numpy as np
import requests
import torch
from g2p_en import G2p
from nemo_text_processing.text_normalization.normalize import Normalizer
from nltk.tokenize import sent_tokenize, TweetTokenizer
from transformers import AutoTokenizer


class DeepPoniesEngine:
    def __init__(self, model_path):
        self.download_models(model_path)
        self.g2p = G2p()
        self.acoustic_model = torch.jit.load(f"{model_path}/acoustic_model.pt")
        self.style_predictor = torch.jit.load(f"{model_path}/style_predictor.pt")
        self.vocoder = torch.jit.load(f"{model_path}/vocoder.pt")
        self.tokenizer = AutoTokenizer.from_pretrained("prajjwal1/bert-tiny")
        self.normalizer = Normalizer(input_case='cased', lang='en')
        self.speaker2id = self.get_speaker2id()
        self.symbol2id = self.get_symbol2id()
        self.lexicon = self.get_lexicon()
        self.word_tokenizer = TweetTokenizer()
        self.acoustic_model.eval()
        self.style_predictor.eval()
        self.vocoder.eval()

    @staticmethod
    def download_models(model_path):
        makedirs(model_path, exist_ok=True)
        nltk.download("punkt")
        base_url = "https://github.com/OpenVoiceOS/ovos-tts-plugin-deepponies/releases/download/0.0.0"

        acoustic_path = f"{model_path}/acoustic_model.pt"
        if not isfile(acoustic_path):
            data = requests.get(f"{base_url}/acoustic_model.pt").content
            with open(acoustic_path, "wb") as f:
                f.write(data)

        style_predictor_path = f"{model_path}/style_predictor.pt"
        if not isfile(style_predictor_path):
            data = requests.get(f"{base_url}/style_predictor.pt").content
            with open(style_predictor_path, "wb") as f:
                f.write(data)

        vocoder_path = f"{model_path}/vocoder.pt"
        if not isfile(vocoder_path):
            data = requests.get(f"{base_url}/vocoder.pt").content
            with open(vocoder_path, "wb") as f:
                f.write(data)

    @staticmethod
    def get_sentences(text):
        sentences = sent_tokenize(text)
        # ["What is this?", "?"] => ["What is this??"]
        merged_sentences = []
        for i, sentence in enumerate(sentences):
            if sentence in [".", "?", "!"]:
                continue
            for next_sentence in sentences[i + 1:]:
                if next_sentence in [".", "?", "!"]:
                    sentence = sentence + next_sentence
                else:
                    break
            merged_sentences.append(sentence)
        return merged_sentences

    @staticmethod
    def get_speaker2id():
        speaker2id = {}
        with open(f"{dirname(__file__)}/assets/speakerCategories.json", "r") as json_file:
            data = json.load(json_file)
        for category in data.keys():
            for item in data[category]["items"]:
                if not item["activated"]:
                    continue
                speaker2id[item["speaker"]] = item["speaker_id"]
        return speaker2id

    @staticmethod
    def get_symbol2id():
        with open(f"{dirname(__file__)}/assets/symbol2id.json", "r") as json_file:
            symbol2id = json.load(json_file)
        return symbol2id

    @staticmethod
    def get_lexicon():
        dic = {}
        with open(f"{dirname(__file__)}/assets/lexicon.txt", "r") as f:
            lines = f.readlines()
        for line in lines:
            split = line.rstrip().split(" ")
            text = split[0].strip()
            phones = split[1:]
            dic[text] = phones
        return dic

    @staticmethod
    def is_arpabet(text):
        if len(text) < 4:
            return False
        return text[:2] == "{{" and text[-2:] == "}}"

    @staticmethod
    def split_arpabet(text):
        splits = re.finditer(r"{{(([^}][^}]?|[^}]}?)*)}}", text)
        out = []
        start = 0
        for split in splits:
            non_arpa = text[start:split.start()]
            arpa = text[split.start():split.end()]
            out = out + [non_arpa] + [arpa]
            start = split.end()
        if start < len(text):
            out.append(text[start:])
        return out

    def synthesize(self, text: str, speaker_name: str, duration_control: float = 1.0,
                   verbose: bool = True) -> np.ndarray:
        waves = []
        text = text.strip()
        speaker_ids = torch.LongTensor([self.speaker2id[speaker_name]])
        if text[-1] not in [".", "?", "!"]:
            text = text + "."

        sentences = self.get_sentences(text)

        for sentence in sentences:
            phone_ids = []
            subsentences_style = []
            for subsentence in self.split_arpabet(sentence):
                if self.is_arpabet(subsentence):
                    for phone in subsentence.strip()[2:-2].split(" "):
                        if "@" + phone in self.symbol2id:
                            phone_ids.append(self.symbol2id["@" + phone])
                else:
                    subsentences_style.append(subsentence)
                    subsentence = self.normalizer.normalize(subsentence, verbose=False)
                    for word in self.word_tokenizer.tokenize(subsentence):
                        word = word.lower()
                        if word in [".", "?", "!"]:
                            phone_ids.append(self.symbol2id[word])
                        elif word in [",", ";"]:
                            phone_ids.append(self.symbol2id["@SILENCE"])
                        elif word in self.lexicon:
                            for phone in self.lexicon[word]:
                                phone_ids.append(self.symbol2id["@" + phone])
                            phone_ids.append(self.symbol2id["@BLANK"])
                        else:
                            for phone in self.g2p(word):
                                phone_ids.append(self.symbol2id["@" + phone])
                            phone_ids.append(self.symbol2id["@BLANK"])

            subsentence_style = " ".join(subsentences_style)
            encoding = self.tokenizer(
                subsentence_style,
                add_special_tokens=True,
                padding=True,
                return_tensors="pt"
            )
            input_ids = encoding["input_ids"]
            attention_mask = encoding["attention_mask"]
            phone_ids = torch.LongTensor([phone_ids])
            with torch.no_grad():
                style = self.style_predictor(input_ids, attention_mask)
                mels = self.acoustic_model(
                    phone_ids,
                    speaker_ids,
                    style,
                    1.0,
                    duration_control
                )
                wave = self.vocoder(mels, speaker_ids, torch.FloatTensor([1.0]))
                waves.append(wave.view(-1))
        full_wave = torch.cat(waves, dim=0).cpu().numpy()
        return full_wave
