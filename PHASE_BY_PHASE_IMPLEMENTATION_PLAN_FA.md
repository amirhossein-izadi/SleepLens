# برنامه اجرایی گام‌به‌گام: مرحله‌بندی خودکار خواب و پیش‌بینی کیفیت خواب

---

## نمای کلی معماری و پایپ‌لاین مهندسی

```
                   فایل‌های خام با فرمت EDF (سیگنال‌های PSG + هیپنوگرام)
                                         │
                                         ▼
        ┌────────────────────────────────────────────────────────┐
        │  فاز ۱: دریافت، برش بیداری‌های ۲۴ ساعته و پیش‌پردازش   │
        │  • تطبیق فایل‌های سیگنال PSG با هیپنوگرام             │
        │  • نگاشت برچسب‌ها به ۵ کلاس استاندارد AASM             │
        │  • برش بیداری‌های طولانی روزانه (بافر ۳۰ دقیقه‌ای)    │
        │  • فیلتر میان‌گذر (۰.۵ تا ۳۵ هرتز) + فیلتر ناچ ۵۰ هرتز │
        │  • قطعه‌بندی به اپوک‌های ۳۰ ثانیه‌ای (۳۰۰۰ نمونه)      │
        │  • نرمال‌سازی مقاوم (IQR) و ذخیره‌سازی کش .npz         │
        └────────────────────────────┬───────────────────────────┘
                                     │
                 ┌───────────────────┴───────────────────┐
                 ▼                                       ▼
  ┌───────────────────────────────┐     ┌───────────────────────────────┐
  │ فاز ۲: مدل پایه جدولی         │     │ فاز ۳: یادگیری عمیق پیوسته    │
  │ • محاسبه طیف توان (Welch PSD) │     │ • استخراج‌کننده ویژگی 1D-CNN   │
  │ • پارامترهای هیورث و آنتروپی  │     │ • لایه‌های دوطرفه BiLSTM      │
  │ • پنجره بافتی (t-1, t, t+1)   │     │ • تابع هزینه وزنی / Focal Loss │
  │ • افزودن سن و جنسیت افراد     │     │ • پردازش مستقیم شکل موج خام   │
  │ • الگوریتم LightGBM / XGBoost │     │ • معماری مدرن TinySleepNet    │
  └──────────────┬────────────────┘     └───────────────┬───────────────┘
                 │                                      │
                 └───────────────────┬──────────────────┘
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  فاز ۴: صاف‌سازی زمانی و پس‌پردازش (Post-Processing)   │
        │  • محاسبه ماتریس تجربی احتمال انتقال مراحل خواب        │
        │  • الگوریتم بهینه‌سازی ویتربی (HMM Viterbi Decoding)   │
        │  • فیلتر میانه ۱ بعدی برای حذف نوسانات لحظه‌ای         │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  فاز ۵: چارچوب اعتبارسنجی بدون نشت اطلاعات (Zero-Leak) │
        │  • تقسیم‌بندی قطعی GroupKFold(5) بر مبنای شناسه بیمار   │
        │  • ارزیابی با Macro-F1 و ضریب کاپای کوهن (Kappa)       │
        │  • ماتریس درهم‌ریختگی ۵ در ۵ و تحلیل خطا               │
        └────────────────────────────┬───────────────────────────┘
                                     │
                                     ▼
        ┌────────────────────────────────────────────────────────┐
        │  فاز ۶: استخراج شاخص‌های بالینی کیفیت خواب            │
        │  • محاسبه کارایی خواب (SE%)، WASO، TST، SOL، SFI       │
        │  • درصد خواب عمیق N3 و درصد خواب رویا REM              │
        │  • سنجش خطای رگرسیون نسبت به واقعیت (MAE و ضریب r)    │
        └────────────────────────────────────────────────────────┘
```

---

## فاز ۱: دریافت، برش بیداری‌های ۲۴ ساعته و پیش‌پردازش سیگنال

### ۱.۱ چالش‌ها و اهداف فنی
داده‌های خام پلی‌سومنوگرافی (PSG) دارای مدت زمان‌های غیر یکسان، نویز برق شهری ۵۰ هرتز، و از همه مهم‌تر **تا ۱۵ ساعت بیداری در طول روز** در زیرمجموعه `sleep-cassette/` هستند. اگر این بیداری‌های روزانه حذف نشوند، بیش از ۷۰٪ کل داده‌ها کلاس بیداری (Wake) خواهد بود و مدل دچار بایاس شدید می‌شود.
هدف فاز ۱ تبدیل این داده‌های خام به آرایه‌های ۳۰ ثانیه‌ای تمیز، فیلترشده و همگام با برچسب‌های ۵ گانه AASM است.

### ۱.۲ مشخصات فنی فاز ۱
* **ورودی:** جفت فایل‌های `SC4ssNE0-PSG.edf` و `SC4ssNEy-Hypnogram.edf` (یا تله‌متری `ST7...`).
* **خروجی:** یک فایل فشرده `.npz` به ازای هر رکورد شامل:
  * `x`: آرایه‌ای به ابعاد `(N_epochs, 3000)` برای سیگنال فیلترشده `EEG Fpz-Cz`.
  * `y`: آرایه برچسب‌های عددی به ابعاد `(N_epochs,)` با مقادیر $\{0, 1, 2, 3, 4\}$.
  * `fs`: نرخ نمونه‌برداری ($100$ هرتز).
  * `subject_id`: شناسه عددی بیمار جهت اعتبارسنجی گروهی.
* **مشخصات فیلترها:**
  * فیلتر میان‌گذر (Bandpass): فیلتر باترورث مرتبه ۴ بدون شیفت فاز (Zero-Phase `filtfilt`) با فرکانس‌های قطع $0.5$ تا $35.0$ هرتز.
  * فیلتر ناچ (Notch): فیلتر دیجیتال IIR در فرکانس $50.0$ هرتز برای حذف نویز برق شهر اروپا ($Q = 30$).
* **نگاشت برچسب‌ها به استاندارد AASM:**
  ```
  'Sleep stage W' -> 0 (بیداری)
  'Sleep stage 1' -> 1 (خواب سبک N1)
  'Sleep stage 2' -> 2 (خواب سبک پایدار N2)
  'Sleep stage 3' -> 3 (خواب عمیق N3)
  'Sleep stage 4' -> 3 (ادغام مرحله ۴ در مرحله ۳ N3)
  'Sleep stage R' -> 4 (خواب رویا REM)
  'Movement time' -> حذف
  'Sleep stage ?' -> حذف
  ```
* **قاعده استاندارد برش بیداری (In-Bed Trimming):**
  * پیدا کردن اندیس اولین اپوک غیربیداری ($t_{\text{first}}$) و آخرین اپوک غیربیداری ($t_{\text{last}}$).
  * نگه‌داشتن فقط ۳۰ دقیقه بیداری قبل از شروع خواب ($60$ اپوک) و ۳۰ دقیقه بیداری پس از پایان خواب ($60$ اپوک) و حذف باقی بیداری‌های قبل از ظهر و عصر.

### ۱.۳ کد پیاده‌سازی کامل فاز ۱

```python
import os
import glob
import pyedflib
import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

def create_filters(fs=100.0, lowcut=0.5, highcut=35.0, notch_freq=50.0, notch_q=30.0):
    nyq = 0.5 * fs
    b_band, a_band = butter(4, [lowcut / nyq, highcut / nyq], btype='band')
    b_notch, a_notch = iirnotch(notch_freq / nyq, notch_q)
    return (b_band, a_band), (b_notch, a_notch)

def preprocess_single_record(psg_path, hyp_path, output_dir, epoch_sec=30, fs_target=100):
    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.basename(psg_path).replace('-PSG.edf', '')
    out_file = os.path.join(output_dir, f"{base_name}.npz")
    if os.path.exists(out_file):
        return out_file

    # ۱. خواندن نشانه‌گذاری‌های هیپنوگرام
    hyp = pyedflib.EdfReader(hyp_path)
    onsets, durations, descriptions = hyp.readAnnotations()
    hyp.close()

    stage_map = {
        'Sleep stage W': 0,
        'Sleep stage 1': 1,
        'Sleep stage 2': 2,
        'Sleep stage 3': 3,
        'Sleep stage 4': 3,
        'Sleep stage R': 4
    }

    epoch_labels = []
    for onset, dur, desc in zip(onsets, durations, descriptions):
        n_ep = int(round(dur / epoch_sec))
        label = stage_map.get(desc, -1) # ۲- برای آپوک‌های فاقد امتیاز یا حرکتی
        epoch_labels.extend([label] * n_ep)
    epoch_labels = np.array(epoch_labels)

    # ۲. خواندن سیگنال مغزی (EEG Fpz-Cz)
    psg = pyedflib.EdfReader(psg_path)
    labels = psg.getSignalLabels()
    ch_idx = labels.index('EEG Fpz-Cz')
    fs = psg.getSampleFrequency(ch_idx)
    raw_signal = psg.readSignal(ch_idx)
    psg.close()

    # ۳. اعمال فیلترهای باترورث و ناچ
    (b_band, a_band), (b_notch, a_notch) = create_filters(fs=fs)
    filtered = filtfilt(b_band, a_band, raw_signal)
    filtered = filtfilt(b_notch, a_notch, filtered)

    # ۴. قطعه‌بندی به اپوک‌های ۳۰ ثانیه‌ای
    samples_per_epoch = int(epoch_sec * fs)
    total_epochs = min(len(filtered) // samples_per_epoch, len(epoch_labels))
    
    x = filtered[:total_epochs * samples_per_epoch].reshape(total_epochs, samples_per_epoch)
    y = epoch_labels[:total_epochs]

    # ۵. برش بیداری‌های اضافه ۲۴ ساعته
    sleep_indices = np.where((y >= 1) & (y <= 4))[0]
    if len(sleep_indices) == 0:
        return None # رکوردی فاقد خواب

    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]
    pad = int(30 * 60 / epoch_sec) # ۶۰ اپوک (معادل ۳۰ دقیقه)

    start_idx = max(0, first_sleep - pad)
    end_idx = min(total_epochs, last_sleep + pad + 1)

    x_trimmed = x[start_idx:end_idx]
    y_trimmed = y[start_idx:end_idx]

    # حذف اپوک‌های نامعتبر (-1)
    valid_mask = y_trimmed != -1
    x_valid = x_trimmed[valid_mask]
    y_valid = y_trimmed[valid_mask]

    # ۶. نرمال‌سازی مقاوم مبتنی بر میانه و دامنه میان‌چارکی (IQR)
    median = np.median(x_valid)
    iqr = np.percentile(x_valid, 75) - np.percentile(x_valid, 25)
    iqr = iqr if iqr > 1e-6 else 1.0
    x_scaled = (x_valid - median) / iqr

    # استخراج شناسه عددی بیمار جهت GroupKFold
    subj_str = base_name[2:5]
    subject_id = int(subj_str)

    np.savez_compressed(
        out_file,
        x=x_scaled.astype(np.float32),
        y=y_valid.astype(np.int64),
        subject_id=subject_id,
        fs=fs
    )
    return out_file
```

---

## فاز ۲: مهندسی ویژگی و مدل پایه جدولی (Track A)

### ۲.۱ هدف فاز ۲
پیش از رفتن به سراغ مدل‌های سنگین یادگیری عمیق، باید یک مدل پایه بسیار سریع و پرقدرت با الگوریتم‌های تقویت گرادیان مانند **LightGBM** یا **XGBoost** بسازیم. این کار در کمتر از ۲ ساعت یک بنچمارک مطمئن و قابل اتکا به دست می‌دهد.

### ۲.۲ ویژگی‌های استخراج‌شده به ازای هر اپوک ۳۰ ثانیه‌ای
* **ویژگی‌های طیف توان فرکانسی (روش Welch PSD):**
  * تفکیک‌پذیری فرکانسی $\Delta f = 0.25$ هرتز با طول پنجره ۴ ثانیه (۴۰۰ نمونه) و همپوشانی ۵۰٪.
  * محاسبه توان مطلق و نسبی در باندهای استاندارد:
    * باند دلتا ($\delta$): $0.5 - 4.0$ هرتز (بیومارکر اصلی خواب عمیق N3).
    * باند تتا ($\theta$): $4.0 - 8.0$ هرتز (بیومارکر خواب‌آلودگی و خواب سبک N1).
    * باند آلفا ($\alpha$): $8.0 - 12.0$ هرتز (بیومارکر بیداری همراه با آرامش).
    * باند سیگما ($\sigma$): $12.0 - 16.0$ هرتز (بیومارکر اختصاصی دوک‌های خواب N2).
    * باند بتا ($\beta$): $16.0 - 30.0$ هرتز (بیومارکر هوشیاری کورتکس مغز و بیداری فعال).
  * نسبت‌های توانی: $\frac{\text{Delta}}{\text{Theta}}$ و $\frac{\text{Delta}}{\text{Beta}}$ و $\frac{\text{Theta}}{\text{Alpha}}$.
* **پارامترهای پیچیدگی سیگنال:**
  * **فعالیت هیورث (Hjorth Activity):** $\text{Var}(x(t))$ نشان‌دهنده توان کل سیگنال.
  * **تحرک‌پذیری هیورث (Hjorth Mobility):** $\sqrt{\frac{\text{Var}(x'(t))}{\text{Var}(x(t))}}$ تخمینی از فرکانس میانگین سیگنال.
  * **پیچیدگی هیورث (Hjorth Complexity):** نسبت تغییرات پهنای باند فرکانسی.
  * **آنتروپی طیفی (Spectral Entropy):** اندازه میزان بی‌نظمی و توزیع انرژی فرکانسی.
* **ویژگی‌های آماری حوزه زمان:** میانگین، انحراف معیار، چولگی، کشیدگی، نرخ عبور از صفر (ZCR).
* **پنجره‌بندی بافتی زمانی (Context Windowing):**
  * مراحل خواب مستقل از هم نیستند. برای هر اپوک در زمان $t$، ویژگی‌های اپوک قبلی ($t-1$) و اپوک بعدی ($t+1$) را در کنار ویژگی‌های خود اپوک قرار می‌دهیم (طول بردار ویژگی ۳ برابر می‌شود). این تکنیک ساده دقت مدل را ۵ تا ۸ درصد جهش می‌دهد!

### ۲.۳ کد پیاده‌سازی استخراج ویژگی و مدلسازی فاز ۲

```python
import numpy as np
import scipy.signal as signal
from scipy.stats import skew, kurtosis
import lightgbm as lgb
from sklearn.metrics import classification_report, f1_score

def compute_epoch_features(epoch, fs=100.0):
    # ۱. آماره‌های حوزه زمان
    mean_val = np.mean(epoch)
    std_val = np.std(epoch)
    skew_val = skew(epoch)
    kurt_val = kurtosis(epoch)
    zcr = np.mean(np.diff(epoch > 0) != 0)

    # ۲. پارامترهای سه‌گانه هیورث
    d1 = np.diff(epoch)
    d2 = np.diff(d1)
    var_zero = np.var(epoch) + 1e-8
    var_d1 = np.var(d1) + 1e-8
    var_d2 = np.var(d2) + 1e-8
    
    activity = var_zero
    mobility = np.sqrt(var_d1 / var_zero)
    complexity = np.sqrt(var_d2 / var_d1) / mobility

    # ۳. طیف توان فرکانسی به روش ولچ
    freqs, psd = signal.welch(epoch, fs=fs, nperseg=int(4 * fs), noverlap=int(2 * fs))
    total_power = np.sum(psd) + 1e-8

    def bandpower(f_low, f_high):
        idx = np.where((freqs >= f_low) & (freqs < f_high))[0]
        return np.sum(psd[idx])

    delta = bandpower(0.5, 4.0)
    theta = bandpower(4.0, 8.0)
    alpha = bandpower(8.0, 12.0)
    sigma = bandpower(12.0, 16.0)
    beta = bandpower(16.0, 30.0)

    # توان‌های نسبی
    rel_delta = delta / total_power
    rel_theta = theta / total_power
    rel_alpha = alpha / total_power
    rel_sigma = sigma / total_power
    rel_beta = beta / total_power

    # آنتروپی طیفی
    psd_norm = psd / total_power
    spec_entropy = -np.sum(psd_norm * np.log2(psd_norm + 1e-12))

    return np.array([
        mean_val, std_val, skew_val, kurt_val, zcr,
        activity, mobility, complexity,
        rel_delta, rel_theta, rel_alpha, rel_sigma, rel_beta,
        spec_entropy,
        (delta + 1e-8) / (theta + 1e-8),
        (delta + 1e-8) / (beta + 1e-8)
    ])

def add_temporal_context(features):
    """افزودن بافت زمانی پنجره‌های (t-1, t, t+1) به ازای هر اپوک"""
    n_epochs, n_feat = features.shape
    context_features = np.zeros((n_epochs, 3 * n_feat), dtype=np.float32)
    for i in range(n_epochs):
        prev_f = features[i - 1] if i > 0 else features[i]
        curr_f = features[i]
        next_f = features[i + 1] if i < n_epochs - 1 else features[i]
        context_features[i] = np.concatenate([prev_f, curr_f, next_f])
    return context_features
```

---

## فاز ۳: مدلسازی توالی با یادگیری عمیق پیوسته (Track B)

### ۳.۱ هدف و معماری شبکه عصبی
برای دستیابی به بالاترین دقت‌های ثبت شده در مقالات معتبر (دقت بالای ۸۴٪ و Macro-F1 بالای ۰.۸۰)، یک شبکه عصبی ترکیبی اند-تو-اند (مشابه **TinySleepNet** یا **DeepSleepNet**) طراحی می‌کنیم که مستقیماً شکل موج خام ۳۰۰۰ نقطه‌ای را دریافت می‌کند.

این مدل از دو بخش اصلی تشکیل شده است:
1. **استخراج‌کننده ویژگی درون اپوک (Intra-Epoch 1D-CNN):** دو شاخه موازی با فیلترهای کوچک (طول ۰.۵ ثانیه معادل ۵۰ نمونه برای دوک‌های خواب و فرکانس‌های بالا) و فیلترهای بزرگ (طول ۴ ثانیه معادل ۴۰۰ نمونه برای امواج آهسته دلتا).
2. **مدل توالی پیوسته بین اپوک‌ها (Inter-Epoch BiLSTM):** لایه‌های بازگشتی دوطرفه LSTM بر روی توالی‌هایی از ۲۰ اپوک متوالی برای یادگیری قواعد انتقال طبیعی فازهای خواب (مثلاً گذار از بیداری به N1 و سپس N2 و N3).

### ۳.۲ کد کامل ماژول PyTorch در فاز ۳

```python
import torch
import torch.nn as nn

class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, stride, pool_size):
        super().__init__()
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels, out_channels, kernel_size, stride=stride, padding=kernel_size//2),
            nn.BatchNorm1d(out_channels),
            nn.ReLU(),
            nn.MaxPool1d(pool_size, stride=pool_size),
            nn.Dropout(0.2)
        )
    def forward(self, x):
        return self.conv(x)

class IntraEpochEncoder(nn.Module):
    """استخراج ویژگی‌های شکل موج ۳۰۰۰ نقطه‌ای در یک اپوک ۳۰ ثانیه‌ای"""
    def __init__(self):
        super().__init__()
        # شاخه اول: تفکیک زمانی بالا برای فرکانس‌های تند (سیگما، بتا)
        self.branch1 = nn.Sequential(
            ConvBlock(1, 64, kernel_size=50, stride=6, pool_size=8),
            ConvBlock(64, 128, kernel_size=8, stride=1, pool_size=4),
            ConvBlock(128, 128, kernel_size=8, stride=1, pool_size=2)
        )
        # شاخه دوم: تفکیک فرکانسی بالا برای امواج آهسته (دلتا، تتا)
        self.branch2 = nn.Sequential(
            ConvBlock(1, 64, kernel_size=400, stride=50, pool_size=4),
            ConvBlock(64, 128, kernel_size=6, stride=1, pool_size=2),
            ConvBlock(128, 128, kernel_size=6, stride=1, pool_size=2)
        )

    def forward(self, x):
        # x: (Batch, 1, 3000)
        out1 = self.branch1(x)
        out2 = self.branch2(x)
        p1 = torch.mean(out1, dim=-1)
        p2 = torch.mean(out2, dim=-1)
        feat = torch.cat([p1, p2], dim=1) # (Batch, 256)
        return feat

class SleepSeqModel(nn.Module):
    """مدل کامل توالی خواب با ترکیب CNN و BiLSTM بر روی توالی L تایی از اپوک‌ها"""
    def __init__(self, num_classes=5, hidden_dim=128):
        super().__init__()
        self.cnn_encoder = IntraEpochEncoder()
        self.lstm = nn.LSTM(
            input_size=256,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            bidirectional=True,
            dropout=0.3
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_dim * 2, 64),
            nn.ReLU(),
            nn.Linear(64, num_classes)
        )

    def forward(self, x_seq):
        # x_seq: (Batch, Seq_Len, 1, 3000)
        B, L, C, S = x_seq.shape
        x_flat = x_seq.view(B * L, C, S)
        feats = self.cnn_encoder(x_flat) # (B*L, 256)
        feats = feats.view(B, L, -1)     # (B, L, 256)

        lstm_out, _ = self.lstm(feats)   # (B, L, hidden_dim*2)
        logits = self.classifier(lstm_out) # (B, L, num_classes)
        return logits
```

---

## فاز ۴: صاف‌سازی زمانی و پس‌پردازش (Post-Processing)

### ۴.۱ هدف فاز ۴
مدل‌ها در پیش‌بینی هر اپوک ممکن است خطاهای تصادفی لحظه‌ای مرتکب شوند؛ مثلاً در میانه یک دوره طولانی خواب عمیق N3، ناگهان یک تک‌اپوک ۳۰ ثانیه‌ای را بیداری یا REM تشخیص دهند که از نظر فیزیولوژی مغز غیرممکن است.
در این فاز، با استفاده از **ماتریس احتمال انتقال حالات خواب** و **الگوریتم بهینه‌سازی سراسری ویتربی (Viterbi)**، ناممکن‌ترین جهش‌های برچسب حذف می‌شوند.

### ۴.۲ کد پیاده‌سازی فاز ۴

```python
import numpy as np
from scipy.signal import medfilt

def build_transition_matrix(y_true_list, num_classes=5):
    """محاسبه ماتریس احتمال تجربی انتقال بین مراحل مختلف خواب"""
    counts = np.zeros((num_classes, num_classes)) + 1e-4 # لاپلاس اسموتینگ
    for seq in y_true_list:
        for i in range(len(seq) - 1):
            s_from = seq[i]
            s_to = seq[i + 1]
            if 0 <= s_from < num_classes and 0 <= s_to < num_classes:
                counts[s_from, s_to] += 1
    trans_matrix = counts / np.sum(counts, axis=1, keepdims=True)
    return trans_matrix

def viterbi_decode(prob_matrix, trans_matrix):
    """
    یافتن محتمل‌ترین توالی فیزیولوژیکی خواب با الگوریتم ویتربی
    prob_matrix: ماتریس احتمال خروجی مدل به ابعاد (N_epochs, 5)
    trans_matrix: ماتریس انتقال حالات خواب (5, 5)
    """
    T, K = prob_matrix.shape
    log_trans = np.log(trans_matrix + 1e-12)
    log_emiss = np.log(prob_matrix + 1e-12)

    viterbi = np.zeros((T, K))
    backpointer = np.zeros((T, K), dtype=int)

    # گام آغازین
    viterbi[0] = log_emiss[0]

    # گام‌های بازگشتی
    for t in range(1, T):
        for j in range(K):
            scores = viterbi[t - 1] + log_trans[:, j] + log_emiss[t, j]
            backpointer[t, j] = np.argmax(scores)
            viterbi[t, j] = np.max(scores)

    # ردیابی مسیر بهینه
    best_path = np.zeros(T, dtype=int)
    best_path[-1] = np.argmax(viterbi[-1])
    for t in range(T - 2, -1, -1):
        best_path[t] = backpointer[t + 1, best_path[t + 1]]

    return best_path
```

---

## فاز ۵: پایپ‌لاین اعتبارسنجی بدون نشت اطلاعات (Zero-Leakage Harness)

### ۵.۱ قانون طلایی: تقسیم‌بندی بر مبنای بیمار (GroupKFold by Subject)
* **هرگز اپوک‌ها را به طور تصادفی تقسیم (Shuffle Split) نکنید!**
* اپوک‌های متعلق به یک شب یک فرد همبستگی بسیار شدیدی دارند. اگر داده‌های یک فرد هم در آموزش و هم در ارزیابی باشند، مدل به جای فیزیولوژی خواب، ویژگی‌های فردی همان شخص را حفظ می‌کند و در داده‌های جدید شکست می‌خورد.
* **الزام:** استفاده از `GroupKFold(n_splits=5)` بر روی شناسه فرد (`subject_id`).

### ۵.۲ کد پایپ‌لاین اعتبارسنجی فاز ۵

```python
import numpy as np
from sklearn.model_selection import GroupKFold
from sklearn.metrics import classification_report, cohen_kappa_score, confusion_matrix, f1_score

def run_group_kfold_cv(X, y, groups, train_fn, predict_fn, n_splits=5):
    gkf = GroupKFold(n_splits=n_splits)
    oof_preds = np.zeros_like(y)
    fold_f1s = []
    fold_kappas = []

    print(f"آغاز اعتبارسنجی متقاطع {n_splits} لایه بر مبنای بیماران...")

    for fold, (train_idx, val_idx) in enumerate(gkf.split(X, y, groups)):
        X_tr, y_tr = X[train_idx], y[train_idx]
        X_va, y_va = X[val_idx], y[val_idx]

        # آموزش مدل در این فولد
        model = train_fn(X_tr, y_tr)

        # پیش‌بینی بر روی داده‌های معتبر
        preds_va = predict_fn(model, X_va)
        oof_preds[val_idx] = preds_va

        f1 = f1_score(y_va, preds_va, average='macro')
        kappa = cohen_kappa_score(y_va, preds_va)
        fold_f1s.append(f1)
        fold_kappas.append(kappa)

        print(f"فولد {fold+1}: Macro F1 = {f1:.4f}, Cohen's Kappa = {kappa:.4f}")

    overall_f1 = f1_score(y, oof_preds, average='macro')
    overall_kappa = cohen_kappa_score(y, oof_preds)
    cm = confusion_matrix(y, oof_preds)

    print("\n=== نتایج نهایی اعتبارسنجی متقاطع ===")
    print(f"Macro F1 کل: {overall_f1:.4f} (میانگین فولدها: {np.mean(fold_f1s):.4f} +/- {np.std(fold_f1s):.4f})")
    print(f"کاپای کوهن کل: {overall_kappa:.4f}")
    print("\nگزارش دقت طبقه‌بندی به تفکیک مراحل:")
    print(classification_report(y, oof_preds, target_names=['W', 'N1', 'N2', 'N3', 'REM'], digits=4))
    print("\nماتریس درهم‌ریختگی (Confusion Matrix):")
    print(cm)
    return oof_preds, fold_f1s
```

---

## فاز ۶: استخراج شاخص‌های بالینی کیفیت خواب

### ۶.۱ هدف و خروجی فاز ۶
پس از آنکه مدل شما هیپنوگرام شبانه (توالی برچسب‌های ۳۰ ثانیه‌ای) را پیش‌بینی کرد، شاخص‌های بالینی استاندارد کیفیت خواب استخراج می‌شوند و با واقعیت مقایسه می‌گردند:

### ۶.۲ کد کامل محاسبه و ارزیابی شاخص‌های کیفیت خواب

```python
import numpy as np

def calculate_quality_metrics(stages, epoch_sec=30):
    sleep_mask = np.isin(stages, [1, 2, 3, 4]) # N1, N2, N3, REM
    sleep_indices = np.where(sleep_mask)[0]

    if len(sleep_indices) == 0:
        return {'SE': 0.0, 'TST': 0.0, 'WASO': 0.0, 'SOL': 0.0, 'pct_N3': 0.0}

    first_sleep = sleep_indices[0]
    last_sleep = sleep_indices[-1]

    tib_min = len(stages) * (epoch_sec / 60)
    tst_min = len(sleep_indices) * (epoch_sec / 60)
    se_pct = (tst_min / tib_min) * 100.0

    sol_min = first_sleep * (epoch_sec / 60)

    # زمان‌های بیداری در میانه خواب
    waso_epochs = np.sum(stages[first_sleep:last_sleep+1] == 0)
    waso_min = waso_epochs * (epoch_sec / 60)

    # مدت و درصد خواب عمیق N3 و خواب رویا REM
    n3_min = np.sum(stages == 3) * (epoch_sec / 60)
    rem_min = np.sum(stages == 4) * (epoch_sec / 60)

    pct_n3 = (n3_min / tst_min) * 100.0 if tst_min > 0 else 0.0
    pct_rem = (rem_min / tst_min) * 100.0 if tst_min > 0 else 0.0

    return {
        'کارایی_خواب_درصد': round(se_pct, 2),
        'کل_زمان_خواب_دقیقه': round(tst_min, 1),
        'زمان_در_بستر_دقیقه': round(tib_min, 1),
        'بیداری_میانه_خواب_WASO': round(waso_min, 1),
        'تاخیر_شروع_خواب_SOL': round(sol_min, 1),
        'درصد_خواب_عمیق_N3': round(pct_n3, 2),
        'درصد_خواب_رویا_REM': round(pct_rem, 2)
    }

def evaluate_quality_metric_prediction(true_hypnograms, pred_hypnograms):
    """سنجش خطای میانگین قدر مطلق (MAE) و ضریب همبستگی پیرسون بین شاخص‌های واقعی و پیش‌بینی‌شده"""
    true_metrics = [calculate_quality_metrics(seq) for seq in true_hypnograms]
    pred_metrics = [calculate_quality_metrics(seq) for seq in pred_hypnograms]

    keys = ['کارایی_خواب_درصد', 'کل_زمان_خواب_دقیقه', 'بیداری_میانه_خواب_WASO', 'درصد_خواب_عمیق_N3']
    results = {}
    for k in keys:
        y_true = np.array([m[k] for m in true_metrics])
        y_pred = np.array([m[k] for m in pred_metrics])
        mae = np.mean(np.abs(y_true - y_pred))
        corr = np.corrcoef(y_true, y_pred)[0, 1]
        results[k] = {'MAE': round(mae, 3), 'Pearson_r': round(corr, 3)}
    return results
```

---

## چک‌لیست اجرایی تیم هکاتون

| فاز | دستاورد / خروجی مشخص | معیار پذیرش و تارگت عددی | اولویت |
| :--- | :--- | :--- | :--- |
| **فاز ۱** | اسکریپت پیش‌پردازش و تولید فایل‌های فشرده `.npz` | ۱۹۷ فایل تمیز با طول ۳۰۰۰ نقطه در هر اپوک | **فوری و حیاتی** |
| **فاز ۲** | استخراج ویژگی‌های فرکانسی/هیورث و مدل LightGBM | Macro-F1 $> 0.74$ و دقت کلی $> 79\%$ | **بالا** |
| **فاز ۳** | شبکه عصبی پیوسته TinySleepNet (1D-CNN + BiLSTM) | Macro-F1 $> 0.80$ و دقت کلی $> 84\%$ | **بالا** |
| **فاز ۴** | الگوریتم پس‌پردازش ویتربی (HMM Viterbi) | بهبود ۱.۵ تا ۲.۵ درصدی در Macro-F1 | **متوسط** |
| **فاز ۵** | پایپ‌لاین ۵ فولده GroupKFold بر مبنای فرد | اعتبارسنجی کاملاً بدون نشت و مطمئن | **حیاتی** |
| **فاز ۶** | ماشین محاسبه معیارهای بالینی خواب (SE, WASO, SOL) | خطای MAE کمتر از ۵٪ در کارایی خواب | **بالا** |
