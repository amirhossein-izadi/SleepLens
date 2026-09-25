Continuous sleep depth index annotation with deep learning yields novel digital biomarkers for sleep health | npj Digital Medicine          

                                                                                                                                                                          

[Skip to main content](#content)

Thank you for visiting nature.com. You are using a browser version with limited support for CSS. To obtain the best experience, we recommend you use a more up to date browser (or turn off compatibility mode in Internet Explorer). In the meantime, to ensure continued support, we are displaying the site without styles and JavaScript.

Advertisement

[![Advertisement](//pubads.g.doubleclick.net/gampad/ad?iu=/285/npjdigitalmed.nature.com/article&sz=728x90&c=-1228800754&t=pos%3Dtop%26type%3Darticle%26artid%3Ds41746-025-01607-0%26doi%3D10.1038/s41746-025-01607-0%26subjmeta%3D1816,375,617,692,700,784%26kwrd%3DQuality+of+life,Sleep+disorders)](//pubads.g.doubleclick.net/gampad/jump?iu=/285/npjdigitalmed.nature.com/article&sz=728x90&c=-1228800754&t=pos%3Dtop%26type%3Darticle%26artid%3Ds41746-025-01607-0%26doi%3D10.1038/s41746-025-01607-0%26subjmeta%3D1816,375,617,692,700,784%26kwrd%3DQuality+of+life,Sleep+disorders)

 [![npj Digital Medicine](https://media.springernature.com/full/nature-cms/uploads/product/npjdigitalmed/header-f049ee6256184b0642aec5ae3c943e37.svg)](/npjdigitalmed)

-   [View all journals](https://www.nature.com/siteindex)
-   [Saved research](/saved-research)
-   [Search](#search-menu)
-   [Account](https://my-profile.springernature.com) [Log in](https://idp.nature.com/auth/personal/springernature?client_id=grover&redirect_uri=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41746-025-01607-0)

-   [Content Explore content](#explore)
-   [About the journal](#about-the-journal)
-   [Publish with us](#publish-with-us)

-   [Sign up for alerts](https://journal-alerts.springernature.com/subscribe?journal_id=41746)
-   [RSS feed](https://www.nature.com/npjdigitalmed.rss)

1.  [nature](/)
2.  [npj digital medicine](/npjdigitalmed)
3.  [articles](/npjdigitalmed/articles?type=article)
4.  article

Continuous sleep depth index annotation with deep learning yields novel digital biomarkers for sleep health

[Download PDF](/articles/s41746-025-01607-0.pdf)

[Download PDF](/articles/s41746-025-01607-0.pdf)

-   Article
-   [Open access](https://www.springernature.com/gp/open-science/about/the-fundamentals-of-open-access-and-open-research)
-   Published: 11 April 2025

# Continuous sleep depth index annotation with deep learning yields novel digital biomarkers for sleep health

-   [Songchi Zhou](#auth-Songchi-Zhou-Aff1)[1](#Aff1),
-   [Ge Song](#auth-Ge-Song-Aff2)[2](#Aff2),
-   [Haoqi Sun](#auth-Haoqi-Sun-Aff3)[3](#Aff3),
-   [Deyun Zhang](#auth-Deyun-Zhang-Aff4)  [ORCID: orcid.org/0000-0002-4041-3083](https://orcid.org/0000-0002-4041-3083)[4](#Aff4),
-   [Yue Leng](#auth-Yue-Leng-Aff5)[5](#Aff5),
-   [M. Brandon Westover](#auth-M__Brandon-Westover-Aff3)[3](#Aff3) &
-   …
-   [Shenda Hong](#auth-Shenda-Hong-Aff1)  [ORCID: orcid.org/0000-0001-7521-5127](https://orcid.org/0000-0001-7521-5127)[1](#Aff1) 

Show authors

[*npj Digital Medicine*](/npjdigitalmed) **volume 8**, Article number: 203 (2025) [Cite this article](#citeas)

[Save article](/articles/s41746-025-01607-0/save-research?_csrf=Mu_D7o8Wycoeb-POj4j8Rrmpbfo9RbkK)

[View saved research](/saved-research)

-   10k Accesses
    
-   15 Citations
    
-   4 Altmetric
    
-   [Metrics details](/articles/s41746-025-01607-0/metrics)
    

## Abstract

Traditional sleep staging categorizes sleep and wakefulness into five coarse-grained classes, overlooking subtle variations within each stage. We propose a deep learning method to annotate continuous sleep depth index (SDI) with existing discrete sleep staging labels, using polysomnography from over 10,000 recordings across four large-scale cohorts. The results showcased a strong correlation between the decrease in sleep depth index and the increase in duration of arousal. Case studies indicated that SDI captured more nuanced sleep structures than conventional sleep staging. Clustering based on the digital biomarkers extracted from the SDI identified two subtypes of sleep, where participants in the disturbed subtype had a higher prevalence of several poor health conditions and were associated with a 33% increased risk of mortality and a 38% increased risk of fatal coronary heart disease. Our study underscores the utility of SDI in revealing more detailed sleep structures and yielding novel digital biomarkers for sleep medicine.

### Similar content being viewed by others

![](https://media.springernature.com/w215h120/springer-static/image/art%3A10.1038%2Fs41598-023-45020-7/MediaObjects/41598_2023_45020_Fig1_HTML.png)

### [Deep learning-based sleep stage classification with cardiorespiratory and body movement activities in individuals with suspected sleep disorders](https://www.nature.com/articles/s41598-023-45020-7?fromPaywallRec=false)

Article Open access 18 October 2023

![](https://media.springernature.com/w215h120/springer-static/image/art%3A10.1038%2Fs42003-025-07794-6/MediaObjects/42003_2025_7794_Fig1_HTML.png)

### [A continuous approach to explain insomnia and subjective-objective sleep discrepancy](https://www.nature.com/articles/s42003-025-07794-6?fromPaywallRec=false)

Article Open access 12 March 2025

![](https://media.springernature.com/w215h120/springer-static/image/art%3Aplaceholder%2Fimages/placeholder-figure-nature.png)

### [Sleep-stage dynamics predict current sleep-disordered breathing and future cardiovascular risk](https://www.nature.com/articles/s41598-026-69352-2?fromPaywallRec=false)

Article Open access 02 September 2026

### Explore related subjects

Discover the latest articles and news in related subjects.

-   [Quality of life](/subjects/quality-of-life)
-   [Sleep disorders](/subjects/sleep-disorders)
-   [Sleep Quality Monitoring and Assessment Techniques](/subjects/sleep-quality-monitoring-and-assessment-techniques)

## Introduction

Sleep is essential to human health, and poor sleep poses threats to people’s daily life[1](/articles/s41746-025-01607-0#ref-CR1 "Tregear, S., Reston, J., Schoelles, K. & Phillips, B. Obstructive sleep apnea and risk of motor vehicle crash: systematic review and meta-analysis. J. Clin. sleep. Med. 5, 573–581 (2009)."),[2](/articles/s41746-025-01607-0#ref-CR2 "Smolensky, M. H., Di Milia, L., Ohayon, M. M. & Philip, P. Sleep disorders, medical conditions, and road accident risk. Accid. Anal. Prev. 43, 533–548 (2011).") and is linked to numerous diseases[3](/articles/s41746-025-01607-0#ref-CR3 "Iranzo, A. & Santamaria, J. Sleep in neurodegenerative diseases. Sleep Medicine: A Comprehensive Guide to Its Development, Clinical Milestones, and Advances in Treatment 271–283 (Springer, 2015)."),[4](/articles/s41746-025-01607-0#ref-CR4 "Tsuno, N., Besset, A. & Ritchie, K. et al. Sleep and depression. J. Clin. psychiatry 66, 1254–1269 (2005)."). Sleep disorders, including sleep fragmentation and obstructive sleep apnea (OSA), are widespread and associated with adverse health outcomes[5](/articles/s41746-025-01607-0#ref-CR5 "Martin, S. E., Engleman, H. M., Deary, I. J. & Douglas, N. J. The effect of sleep fragmentation on daytime function. Am. J. Respir. Crit. Care Med. 153, 1328–1332 (1996)."),[6](/articles/s41746-025-01607-0#ref-CR6 "Strollo Jr, P. J. & Rogers, R. M. Obstructive sleep apnea. N. Engl. J. Med. 334, 99–104 (1996)."). In sleep medicine, sleep staging based on polysomnography (PSG) has been an indispensable part of revealing sleep structures for disease diagnosis[7](#ref-CR7 "Boeve, B. F. Idiopathic rem sleep behaviour disorder in the development of parkinson’s disease. Lancet Neurol. 12, 469–482 (2013)."),[8](#ref-CR8 "Stephansen, J. B. et al. Neural network analysis of sleep stages enables efficient diagnosis of narcolepsy. Nat. Commun. 9, 5229 (2018)."),[9](/articles/s41746-025-01607-0#ref-CR9 "Bohnen, N. I. & Hu, M. Sleep disturbance as potential risk and progression factor for parkinson’s disease. J. Parkinson’s. Dis. 9, 603–614 (2019)."). According to the American Academy of Sleep Medicine (AASM) guidelines[10](/articles/s41746-025-01607-0#ref-CR10 "Berry, R. B. et al. The aasm manual for the scoring of sleep and associated events. Rules, Terminol. Tech. Specif., Darien, Ill., Am. Acad. Sleep. Med. 176, 7 (2012)."), sleep and wakefulness are classified into five stages: wake (W), rapid eye movement (REM) (R), non-REM stage 1 (N1), non-REM stage 2 (N2), and non-REM stage 3 (N3) for every non-overlapping 30-second. Despite its importance, manual PSG scoring is labor-intensive and prone to variability[11](/articles/s41746-025-01607-0#ref-CR11 "Magalang, U. J. et al. Agreement in the scoring of respiratory events and sleep among international sleep centers. Sleep 36, 591–596 (2013)."),[12](/articles/s41746-025-01607-0#ref-CR12 "Younes, M., Raneri, J. & Hanly, P. Staging sleep in polysomnograms: analysis of inter-scorer variability. J. Clin. Sleep. Med. 12, 885–894 (2016)."). Consequently, numerous machine-learning methods have been developed to automate sleep staging with performance comparable to human experts[13](#ref-CR13 "Biswal, S. et al. Sleepnet: automated sleep staging system via deep learning. arXiv preprint arXiv:1707.08262 (2017)."),[14](#ref-CR14 "Biswal, S. et al. Expert-level sleep scoring with deep neural networks. J. Am. Med. Inform. Assoc. 25, 1643–1650 (2018)."),[15](#ref-CR15 "Perslev, M., Jensen, M., Darkner, S., Jennum, P. J. & Igel, C. U-time: a fully convolutional network for time series segmentation applied to sleep staging. Adv. Neural Inform. Processi. Syst. 32 (2019)."),[16](#ref-CR16 "Sridhar, N. et al. Deep learning for automated sleep staging using instantaneous heart rate. NPJ Digital Med. 3, 106 (2020)."),[17](/articles/s41746-025-01607-0#ref-CR17 "Tveit, J. et al. Automated interpretation of clinical electroencephalograms using artificial intelligence. JAMA Neurol. 80, 805–812 (2023)."). However, current sleep staging is too coarse to accurately reflect sleep depth due to detailed differences in sleep structures within the same stages[18](#ref-CR18 "Uchida, S., Maloney, T., March, J., Azari, R. & Feinberg, I. Sigma (12–15 hz) and delta (0.3–3 hz) eeg oscillate reciprocally within nrem sleep. Brain Res. Bull. 27, 93–96 (1991)."),[19](#ref-CR19 "Uchida, S., Maloney, T. & Feinberg, I. Beta (20–28 hz) and delta (0.3–3 hz) eegs oscillate reciprocally across nrem and rem sleep. Sleep 15, 352–358 (1992)."),[20](/articles/s41746-025-01607-0#ref-CR20 "Bonnet, M. & Arand, D. Heart rate variability: sleep stage, time of night, and arousal influences. Electroencephalogr. Clin. Neurophysiol. 102, 390–396 (1997).").

A continuous measure of sleep depth, reflecting the likelihood of being aroused from sleep, holds more value than discrete sleep staging results with respect to research on populations with sleep fragmentation. It has traditionally been studied using external stimuli[21](/articles/s41746-025-01607-0#ref-CR21 "Johnson, L., Church, M., Seales, D. & Rossiter, V. Auditory arousal thresholds of good sleepers and poor sleepers with and without flurazepam. Sleep 1, 259–270 (1978)."),[22](/articles/s41746-025-01607-0#ref-CR22 "Gleeson, K., ZWILLlCH, C. W. & White, D. P. The influence of increasing ventilatory effort on arousal from sleep1-3. Am. Rev. Respir. Dis. 142, 295–300 (1990)."). These methods may fail to reflect instantaneous arousal because of the application of stimulus over a long period when sleep depth can already change. Electroencephalogram (EEG) delta power is commonly considered to be closely related to sleep depth. Notably, the odds ratio product (ORP) is introduced as a continuous estimate of sleep depth, derived from the relationship between EEG power in different frequencies[23](/articles/s41746-025-01607-0#ref-CR23 "Younes, M. et al. Odds ratio product of sleep eeg as a continuous measure of sleep state. Sleep 38, 641–654 (2015)."). Subsequent studies have validated its effectiveness as an index of sleep depth[24](#ref-CR24 "Meza-Vargas, S., Giannouli, E. & Younes, M. Enhancements to the multiple sleep latency test. Nat. Sci. Sleep 8, 145–158 (2016)."),[25](#ref-CR25 "Qanash, S., Giannouli, E. & Younes, M. Assessment of intervention-related changes in non-rapid-eye-movement sleep depth: importance of sleep depth changes within stage 2. Sleep. Med. 40, 84–93 (2017)."),[26](#ref-CR26 "Younes, M., Soiferman, M., Thompson, W. & Giannouli, E. Performance of a new portable wireless sleep monitor. J. Clin. Sleep. Med. 13, 245–258 (2017)."),[27](#ref-CR27 "Younes, M., Azarbarzin, A., Reid, M., Mazzotti, D. R. & Redline, S. Characteristics and reproducibility of novel sleep eeg biomarkers and their variation with sleep apnea and insomnia in a large community-based cohort. Sleep 44, zsab145 (2021)."),[28](/articles/s41746-025-01607-0#ref-CR28 "Younes, M. et al. Sleep architecture based on sleep depth and propensity: patterns in different demographics and sleep disorders and association with health outcomes. Sleep 45, zsac059 (2022)."). Recent research demonstrates that principal component analysis (PCA) on pre-computed sleep-stage clusters can distinguish sleep stages in a low-dimensional sub-space[29](/articles/s41746-025-01607-0#ref-CR29 "Metzner, C. et al. Extracting continuous sleep depth from eeg data without machine learning. Neurobiol. Sleep. Circadian Rhythms 14, 100097 (2023)."). These methods, however, rely solely on EEG data, while AASM recommends using PSG for a comprehensive analysis[10](/articles/s41746-025-01607-0#ref-CR10 "Berry, R. B. et al. The aasm manual for the scoring of sleep and associated events. Rules, Terminol. Tech. Specif., Darien, Ill., Am. Acad. Sleep. Med. 176, 7 (2012)."). Additionally, these measures often involve manually computed features that may not capture nuanced sleep structures.

Artificial intelligence (AI), particularly deep learning[30](/articles/s41746-025-01607-0#ref-CR30 "LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. Nature 521, 436–444 (2015)."), has become increasingly popular in sleep medicine[31](/articles/s41746-025-01607-0#ref-CR31 "Goldstein, C. A. et al. Artificial intelligence in sleep medicine: an american academy of sleep medicine position statement. J. Clin. Sleep. Med. 16, 605–607 (2020)."),[32](/articles/s41746-025-01607-0#ref-CR32 "Bandyopadhyay, A. & Goldstein, C. Clinical applications of artificial intelligence in sleep medicine: a sleep clinician’s perspective. Sleep. Breath. 27, 39–55 (2023)."). Specifically for sleep depth annotation, AI has the potential to process vast amounts of PSG data and uncover detailed information overlooked by clinicians using some off-the-shelf sleep labels (e.g., sleep staging labels and respiratory events). Given the ordinal nature of Non-Rapid Eye Movement (NREM) stages, expert-labeled staging results can help derive a measure of sleep depth. However, the existing sleep staging labels are coarse-grained as five discrete classes, prohibiting direct supervised training to generate a continuous sleep depth measure. Inspired by the idea of learning to rank widely used in various fields[33](#ref-CR33 "Liu, T.-Y. et al. Learning to rank for information retrieval. Found. Trends® Inf. Retr. 3, 225–331 (2009)."),[34](#ref-CR34 "Karatzoglou, A., Baltrunas, L. & Shi, Y. Learning to rank for recommender systems. Proce. 7th ACM Conference on Recommender Systems 493–494 (Association for Computing Machinery, 2013)."),[35](/articles/s41746-025-01607-0#ref-CR35 "Agarwal, A. et al. Learning to rank for robust question answering. Proc. 21st ACM international conference on Information and knowledge management 833–842 (Association for Computing Machinery, 2012)."), we may use ranking-based methods to guide the model to assign higher values to sleep epochs labeled with sleep stages conventionally regarded as deeper sleep. The stages from N1 to N3 represent progressively deeper sleep[36](/articles/s41746-025-01607-0#ref-CR36 "Patel, A. K., Reddy, V., Shumway, K. R. & Araujo, J. F. Physiology, sleep stages. In StatPearls [Internet] (StatPearls Publishing, 2022)."), fitting well within the learning-to-rank framework. The REM stage, due to its unique significance in clinical settings[37](#ref-CR37 "Ferini-Strambi, L. & Zucconi, M. Rem sleep behavior disorder. Clin. Neurophysiol. 111, S136–S140 (2000)."),[38](#ref-CR38 "Postuma, R., Gagnon, J.-F., Rompre, S. & Montplaisir, J. Severity of rem atonia loss in idiopathic rem sleep behavior disorder predicts parkinson disease. Neurology 74, 239–244 (2010)."),[39](/articles/s41746-025-01607-0#ref-CR39 "McCarter, S. J., St. Louis, E. K. & Boeve, B. F. Rem sleep behavior disorder and rem sleep without atonia as an early manifestation of degenerative neurological disease. Curr. Neurol. Neurosci. Rep. 12, 182–192 (2012)."), requires careful handling in comparisons with NREM stages. Nevertheless, REM is deeper than wakefulness and can be integrated into the ranking process, though its comparison with other NREM stages needs caution. Even though the acquirement of the whole-night sleep depth index can serve as a valuable tool to help clinicians inspect the sleep structure from a more detailed perspective, there is no guideline on how to use this whole-night sleep depth index for routine clinical practice for sleep health. Since the whole-night sleep depth index is a type of time series, we can extract several features such as basic time-domain features or complexity-related features as novel digital biomarkers, and investigate their indications for various health conditions.

To address the aforementioned challenges, we employed a carefully designed pairwise ranking loss to learn the ordinal relations between the NREM sleep stages and between the wake and REM stages, enabling flexible sleep depth annotation within the same stage. This approach will yield a continuous value from 0 to 1, with the larger value indicating deeper sleep for each 30-s PSG epoch. Extensive validations showed that the decrease in sleep depth index is closely associated with the increase in the duration of arousal in the next 30 seconds (Pearson correlation coefficient >0.99). Taking the unique role of REM in sleep medicine[37](#ref-CR37 "Ferini-Strambi, L. & Zucconi, M. Rem sleep behavior disorder. Clin. Neurophysiol. 111, S136–S140 (2000)."),[38](#ref-CR38 "Postuma, R., Gagnon, J.-F., Rompre, S. & Montplaisir, J. Severity of rem atonia loss in idiopathic rem sleep behavior disorder predicts parkinson disease. Neurology 74, 239–244 (2010)."),[39](/articles/s41746-025-01607-0#ref-CR39 "McCarter, S. J., St. Louis, E. K. & Boeve, B. F. Rem sleep behavior disorder and rem sleep without atonia as an early manifestation of degenerative neurological disease. Curr. Neurol. Neurosci. Rep. 12, 182–192 (2012).") into consideration, we coupled the sleep depth annotation with a REM classification for comprehensive sleep profiling. Then we inspected the nuanced differences in sleep depth index across the same and varied sleep stages, presenting that the same sleep stage could be better distinguished by sleep depth index instead of sleep staging. The whole-night continuous sleep depth index, as a type of time series, allows the extraction of various features as novel sleep biomarkers. We used the Gaussian mixture model to obtain two clusters with the extracted digital biomarkers, namely the normal sleep subtype and the disturbed sleep subtype. Subsequent analyses showcased that the disturbed sleep subtype was associated with several poor health conditions including hypertension, sleep apnea, and so on. Figure [1](/articles/s41746-025-01607-0#Fig1) displays an overview of the study.

**Fig. 1: General overview of the study.**

![Fig. 1: General overview of the study.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig1_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/1)

**a** Four channels of physiological signals from PSG, EEG, EOG, EMG, and ECG were used in this study. The MESA, MROS, and CFS cohorts were used as the training set and interval validation set and the SHHS cohort was used as the external validation set. **b** Using a deep learning method, the neural network was able to transform the discrete sleep staging into a continuous sleep depth index. **c** There were several interesting pieces of evidence found in the sleep depth index, which added new insights into the understanding of sleep structure. Digital biomarkers extracted from the sleep depth index were used for clustering, resulting in sleep subtypes exhibiting varied health outcomes. A web app was provided for continuous SDI annotation supporting EDF-format inputs. PSG Polysomnography, EEG Electroencephalography, EOG Electrooculography, EMG Electromyography, ECG Electrocardiography, SDI Sleep depth index, RB Ratio below a certain threshold, CV Coefficient of variation, AP Proportion of area under the sleep depth index curve, SK Skewness, MDR Mean depth value of the REM sleep epochs, PR Proportion of REM to the total sleep duration, APPe Approximate entropy, DETRf Detrended fluctuation analysis.

In summary, our contributions are as follows:

-   We propose a first-of-its-kind deep learning method to annotate the sleep depth index using the PSG data and existing sleep staging labels in an end-to-end way. The model structure supports scalable training on large-scale sleep data. We also deploy an easy-to-use web application for automatic annotation of the sleep depth index.
    
-   Experiments on large-scale sleep cohorts and external validations demonstrated the effectiveness of our method. The decrease in the sleep depth index was strongly correlated to the increase in the duration of arousal, and the sleep depth index presented more nuanced sleep structures than conventional sleep staging.
    
-   The whole-night sleep depth index time series yielded novel digital sleep biomarkers that were used for clustering. The resultant disturbed sleep subtype was significantly associated with a higher prevalence of several poor health conditions and an increased risk of all-cause mortality and fatal coronary heart disease.
    

## Results

### Data curation and deep learning model development

In this study, we mainly aimed to use a deep learning method to annotate continuous sleep depth using the existing sleep staging labels. Specifically, EEG, Electromyography (EMG), Electrooculography (EOG), and Electrocardiography (ECG) were extracted from the PSG as the input physiological signals for the model. We then converted sleep staging results labeled by the clinicians to ranks to compute the ranking loss and utilized the REM label for the REM classification loss. The MESA, MROS, and CFS cohorts were used as the training set of the deep learning model, comprising 3984 participants, and the other 1708 participants were organized into the internal validation set. The data from the SHHS cohorts was not included in the model training and thus acted as the external validation set. When trained, the deep learning model enables the transition from the discrete sleep stages to the continuous sleep depth index ranging from 0 to 1. We then analyzed the results related to the learned sleep depth index in the following sections.

### Distribution of sleep depth index and concordance across sleep stages

Supplementary Fig. [1](/articles/s41746-025-01607-0#MOESM1) presents boxplots showing the distribution of the sleep depth index across the five sleep stages for each cohort. For the W stage, most sleep depth indices were below 0.1. Conversely, the deepest stage, N3, generally exhibited the highest sleep depth values, consistent with conventional expectations. Interestingly, some high sleep depth values also appeared in the N2 stage and the REM stage. The N1 stage, representing a deeper sleep than wakefulness, showcased sleep depth values mostly ranging between 0.1 and 0.5. Both the N2 and REM stages displayed a wide range of sleep depth indices, indicating varying sleep structures within the same annotated stage. In Supplementary Table [1](/articles/s41746-025-01607-0#MOESM1), the first column showed the Spearman’s rank correlation coefficient between the sleep depth index and the four sleep stages (W, N1, N2, and N3), which were encoded as progressively deeper sleep transitions (REM stage was not incorporated since its ordinal relation to other NREM stages could not be ascertained). The correlations, all exceeding 0.85, demonstrated good averaged concordance between the sleep depth index and traditional sleep staging results.

To comprehensively showcase whole-night sleep profiles, we have integrated sleep depth annotation with the REM classification. The classification results, detailed in Supplementary Table [1](/articles/s41746-025-01607-0#MOESM1), were presented as the area under the receiver operating characteristic (AUROC) values. Overall, the micro-averaged AUROC for the four cohorts was 0.978, with a 95% confidence interval (CI) ranging from 0.977 to 0.979. For the three internal testing sets, the AUROC values were as follows: 0.990 (95% CI \[0.988,0.991\]) for the MESA dataset, 0.984 (95% CI \[0.981,0.986\]) for the MROS dataset, and 0.985 (95% CI \[0.981,0.989\]) for the CFS dataset. On the external validation SHHS dataset, the AUROC value was 0.975 (95% CI \[0.974,0.976\]), demonstrating the robustness of the REM classification part and its ability to generalize well across different datasets. Notably, the third column in Supplementary Table [1](/articles/s41746-025-01607-0#MOESM1) presents the REM classification without training together with the sleep depth annotation task, where the classification performance was universally slightly worse than those in the second column, suggesting that the joint training model structure could enhance the representation learning of PSG data.

### Case studies for nuanced sleep structures shown in sleep depth index while not in traditional sleep staging

In this section, we investigated the nuanced sleep structures and patterns captured by the proposed sleep depth index, while overlooked by the traditional sleep staging methods. In Fig. [2](/articles/s41746-025-01607-0#Fig2)a, the three 30-second epochs were all labeled with the N2 stage by the clinicians. However, apparently different sleep patterns could be noticed. The first epoch featured high-frequency EEG and high-amplitude EMG, resembling a waking state but also showing a representative N2 stage K-complex. The second epoch presented significantly lower EMG amplitude and more low-frequency and high-amplitude EEG waves, indicating deeper sleep states. The third epoch was labeled with a larger sleep depth index, where more low-frequency EEG patterns were observed. Furthermore, in Fig. [2](/articles/s41746-025-01607-0#Fig2)b, the three 30-s epochs were all labeled as the REM stage but characterized with varied sleep depth index by our model. We were able to observe more lower-frequency and higher-amplitude EEG features in the epochs with larger sleep depth values. In addition, larger sleep depth indexes were associated with more evident eye movements showcased by the EOG. The N1 stage, which suffers from poor inter-rater reliability, has been challenging for existing sleep staging methods due to the subtle differences between N1 and N2. In Fig. [2](/articles/s41746-025-01607-0#Fig2)c, although both the first epoch and the second epoch were recognized as N1, the sleep depth index would assign a higher value to the second epoch in relation to the lower-frequency and higher-amplitude EEG pattern. Nevertheless, the physiological signals in the third epoch, which was labeled with the N2 stage, resembled those from the second epoch and thus shared a close sleep depth index.

**Fig. 2: Cases of varied patterns of the physiological signals across the sleep stages.**

![Fig. 2: Cases of varied patterns of the physiological signals across the sleep stages.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig2_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/2)

**a** The three stages belonged to the same N2 stage but the sleep depth values differed. The sleep depth index better captured the lower frequency feature of deep sleep and the smaller magnitude of EMG. **b** The three stages belonged to the same REM stage but the sleep depth values differed. The sleep depth index better captured the lower frequency feature of deep sleep and the larger magnitude of EOG. **c** The first two stages belonged to the N1 stage but the second one was labeled with a slightly larger sleep depth index. The third stage shared similar patterns with the second stage, but it was labeled as the N2 stage, where the sleep depth values were close. SDI Sleep depth index, EEG Electroencephalography, EOG Electrooculography, EMG Electromyography, ECG Electrocardiography.

### The decrease in sleep depth index and the increase in duration of arousal was highly correlated

Arousal during sleep represents a shift from deep sleep to light sleep or from sleep to wakefulness[40](/articles/s41746-025-01607-0#ref-CR40 "Scammell, T. E., Arrigoni, E. & Lipton, J. O. Neural circuitry of wakefulness and sleep. Neuron 93, 747–765 (2017)."). A low likelihood of arousal indicates deeper sleep depth, making it less likely for the sleeper to be awakened. For the four cohorts studied, arousal events were annotated with their start and duration times. We then defined the duration of arousal for a certain 30-second epoch as the proportion of the arousal duration within that epoch. The decrease in the sleep depth index was computed by subtracting the value at time *t* from the value at time *t* − 1. We created deciles for the annotated sleep depth index, resulting in ten equal intervals. We then averaged the arousal durations within each interval, with error bars representing two-sided confidence intervals. As shown in Fig. [3](/articles/s41746-025-01607-0#Fig3), the linear regression analysis for each cohort revealed strong correlations between the decrease in sleep depth index and the increase in the duration of arousal. Specifically, the Pearson correlation coefficients were 0.9913 for SHHS, 0.9968 for CFS, 0.9955 for MESA, and 0.9977 for MROS. It could be noted that larger decreases in sleep depth correspond to broader confidence intervals, probably attributed to the fewer PSG epochs with long arousal durations. Moreover, we investigated this linear relation with more bins (100) split shown in Supplementary Fig. [2](/articles/s41746-025-01607-0#MOESM1), where prominent correlations could still be found.

**Fig. 3: The correlation between the decreased magnitude of the sleep depth index and the increase in the duration of arousal.**

![Fig. 3: The correlation between the decreased magnitude of the sleep depth index and the increase in the duration of arousal.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig3_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/3)

**a** The SHHS cohort. **b** The CFS cohort. **c** The MESA cohort. **d** The MROS cohort. The duration of arousal was computed as the proportion of arousal duration in a 30-s epoch. We calculated the ten deciles of 0 to 1 and averaged the values in each interval for linear regression fitting. The red dotted line represented the diagonal line. The average relationship was almost perfectly linear.

### Clustering based on the digital biomarkers derived from sleep depth index resulted in two subtypes with different health conditions and outcomes

As for the whole-night continuous sleep depth index for each subject, we extracted a set of time series features as the novel digital biomarkers. In the time domain, the coefficient of variation (CV) and skewness (SK) were computed. Based on the physiological nature of the sleep depth index, we then devised several intuitive features to reflect the sleep states. The first was the ratio below a certain threshold (RB), indicating the proportion of shallow sleep during the night. We set 0.2 as the threshold in our study. The second one was the proportion of area under the sleep depth index curve (AP), computed by dividing the integration value of the sleep depth index by the total sleep duration. This feature showcased the efficiency of sleep more accurately than the conventional sleep efficiency (SE) metric, which was computed as the ratio of sleep duration to the in-bed period. The approximate entropy (APPe) and the detrended fluctuation analysis results (DETRf) were extracted to analyze the complexity dimension of the sleep depth index. Since we have acquired the REM classification results at the same time, the mean depth value of the REM sleep epochs (MDR) and the proportion of REM to the total sleep duration (PR) were also extracted. Subsequently, these digital biomarkers were used as input for the Gaussian mixture model for clustering, resulting in two subtypes of sleep, namely the normal sleep subtype and the disturbed sleep subtype.

In Fig. [4](/articles/s41746-025-01607-0#Fig4), the effect sizes estimates with 95% CIs for demographic, traditional metrics, SDI-based features, and several health outcomes are displayed. The detailed values of the effect sizes and the mean values were stored in Supplementary Table [3](/articles/s41746-025-01607-0#MOESM1). Generally, for the three cohorts, SHHS, CFS, and MROS, participants in the disturbed sleep group were older and had a large Body Mass Index (BMI), but this finding was only prominent in the CFS cohort. For the SHHS cohort and CFS cohort, male participants were more likely to be in the disturbed subtype. Regarding traditional sleep metrics, participants in the disturbed sleep group had significantly lower sleep efficiency, as indicated by large effect sizes. They also tended to have longer sleep latency (SL), though this tendency was much weaker. As for the SDI features, the disturbed sleep featured larger RB and smaller AP, indicating a more dominant ratio of shallow sleep and lower sleep efficiency than the normal sleep group. The larger CV in the disturbed sleep group showcased more dispersed patterns than the normal and the larger skewness indicated more frequent or extremely high values. The normal sleep group was characterized by larger MDR and PR, presenting deeper sleep in the REM and longer duration of the REM stage. Notably, the normal sleep group presented larger APPe and DETRf, showcasing a higher level of complexity when compared with the disturbed group. There was an apparent opposite trend for the CV feature and the complexity-based features. It was suspected that the CV reflects more on the variation of regular disturbance across the night and that those with disturbed sleep patterns were frequently affected by these interruptions. On the other side, as measures of complexity, APPe and DETRf presented more nuanced sleep structures similar to the heart rate variability (HRV) for ECG data, where reduced HRV has been shown to be associated with some poor health outcomes[41](/articles/s41746-025-01607-0#ref-CR41 "Kleiger, R. E., Miller, J. P., Bigger Jr, J. T. & Moss, A. J. Decreased heart rate variability and its association with increased mortality after acute myocardial infarction. Am. J. Cardiol. 59, 256–262 (1987)."),[42](/articles/s41746-025-01607-0#ref-CR42 "Bigger Jr, J. T. et al. Frequency domain measures of heart period variability and mortality after myocardial infarction. Circulation 85, 164–171 (1992).").

**Fig. 4: Effect size estimates with 95% CIs for demographic, SDI-based features, and several health outcomes.**

![Fig. 4: Effect size estimates with 95% CIs for demographic, SDI-based features, and several health outcomes.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig4_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/4)

The region above the dashed line with blue data points was about the comparison of continuous variables, using the t-test to compare the between-group differences and Cohen’s d as the measure of effect size. The effect size was computed by subtracting the value of the normal sleep group from the disturbed sleep group. The lower region was about the comparison of categorical variables. For sex, males were coded as 1 and females as 0. For outcomes, the presence of a specific outcome was recorded as 1. The Chi-squared test was used to compare the between-group differences for the sex variable and odds ratio was utilized as the measure of effect size. Logistic regression was used to estimate the odds ratio of the outcome variables, adjusting for age, BMI, sex, SE, and SL. The disturbed sleep group was regarded as value 1 when computing the effect size. BMI Body Mass Index, SE Sleep efficiency, SL Sleep latency, SDI Sleep depth index, RB Ratio below a certain threshold, CV Coefficient of variation, AP Proportion of area under the sleep depth index curve, SK Skewness, MDR Mean depth value of the REM sleep epochs, PR Proportion of REM to the total sleep duration, APPe Approximate entropy, DETRf Detrended fluctuation analysis, CVD Cardiovascular disease.

For the two subtypes, the differences in the prevalence of several health were investigated in the lower region of Fig. [4](/articles/s41746-025-01607-0#Fig4) labeled with red. Logistic regression controlling for age, BMI, sex, SE, and SL was used to estimate the odds ratio (OR) with 95%CI. Sleep apnea was defined as having an Apnea-Hypopnea Index (AHI) larger than 5. The results of poor subjective sleep quality and insomnia were sourced from the morning surveys of the corresponding cohorts. Note that there was no outcome of cardiovascular disease (CVD) for the MROS cohort. We could see from Fig. [4](/articles/s41746-025-01607-0#Fig4) that the disturbed group across the three cohorts showcased a significantly higher prevalence of sleep apnea, with the odds ratio ranging from 1.15 to 1.55. Poor subjective sleep quality was also significantly associated with the disturbed subtype, with the odds ratio being 2.35(95% CI 1.37–4.0) for the CFS cohort, and 2.23 (95% CI 1.63–3.06) for the MROS cohort, but not significant for the SHHS cohort. Insomnia occurred more frequently for participants in the CFS and MROS cohort with the disturbed subtypes, where the odds ratios were 2.01 and 1.58. The difference in the prevalence of diabetes between the two subtypes was not statistically significant across the three cohorts. CVD was more prevalent in the disturbed subtype than the normal subtype for the SHHS cohort (OR 1.25 95% 1.03–1.53), but not statistically significant for the CFS cohort. Populations belonging to the disturbed subtype were associated with a higher prevalence of hypertension for the SHHS (OR 1.21 95% 1.03–1.43).

As for the SHHS cohort, time-to-event data was extracted for survival analysis of the clustered two subtypes. In Fig. [5](/articles/s41746-025-01607-0#Fig5), Kaplan–Meier survival estimates provided a visual interpretation of the crude probability of all-cause mortality and fatal coronary heart disease. Log-rank tests showcased significant differences between the two subtypes in the survival probability (*p* < 0.001 for both all-cause mortality and fatal coronary heart disease). From the results, participants in the disturbed subtype had a significantly lower survival probability than the normal subtype. The Cox regression model was then used to determine the hazard ratios (HRs) and 95% confidence intervals to compare the risks in the normal sleep and disturbed sleep groups, adjusting for age, BMI, sex, SE, and SL. For all-cause mortality, the disturbed sleep group was associated with a 33% (hazard ratio 1.33, 95% CI 1.16–1.53, *p* < 0.001) increased risk compared with the normal sleep group. For the fatal coronary heart disease, participants with the disturbed subtype suffered a 38% (hazard ratio 1.38, 95% CI 1.01–1.90, *p* = 0.046) increased risk with respect to the other normal subtype.

**Fig. 5: Survival outcomes by clinical subtype.**

![Fig. 5: Survival outcomes by clinical subtype.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig5_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/5)

Kaplan–Meier curves across the two subtypes for **a** all-cause mortality **b** fatal coronary heart disease. HR hazard ratio, CI confidence interval.

In Fig. [6](/articles/s41746-025-01607-0#Fig6), we investigated the differences in SDI patterns for the two clustered subtypes with some instances. We presented the full-night SDI annotations and hypnograms for four SHHS patients. The boxes on the right displayed some metrics such as total sleep time (TST), sleep efficiency, AHI, area under the sleep depth index curve (AUC), and AP. Specifically, for Fig. [6](/articles/s41746-025-01607-0#Fig6)a, two participants with similar structure hypnograms but belonging to varied clustered sleep subtypes were compared. The participant with disturbed sleep was labeled with a sleep efficiency of 94%, a little larger than the one displayed in the upper sub-figure of 93%. However, the latter showcased a larger AP (0.46) than the former (0.253), and in the plots of SDI, we could observe that the participant with disturbed sleep had very shallow sleep in the second half of the night, which would not be discovered by the traditional sleep staging method. In Fig. [6](/articles/s41746-025-01607-0#Fig6)b, a patient characterized by constant arousal and severe sleep apnea featured shallow sleep across the whole night, ending with a very low AP (0.218) and AUC (233.14) but still a high sleep efficiency (85%) and high total sleep time (450.5 min). Next for the participant with the disturbed subtype as shown in Fig. [6](/articles/s41746-025-01607-0#Fig6)c, no REM or N3 were identified, and no sleep cycles were observed. Though the participants had a high AUC and AP, the sleep pattern fiercely fluctuated from deep sleep to shallow and vice versa, which was less obvious in the frequent transitions between the wake and N2 stages as shown in the hypnogram.

**Fig. 6: Plots of the whole-night SDI along with the expert-labeled hypnogram, where the degree of the gray color indicates the proportion of arousal in a 30-s epoch.**

![Fig. 6: Plots of the whole-night SDI along with the expert-labeled hypnogram, where the degree of the gray color indicates the proportion of arousal in a 30-s epoch.](//media.springernature.com/lw685/springer-static/image/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_Fig6_HTML.png)

[Full size image](/articles/s41746-025-01607-0/figures/6)

In the information box on the right, sleep metrics with \* are derived from the sleep depth index. **a** Two participants belonging to two different sleep subtypes had close sleep efficiency metrics but significantly different AUC and AP. **b** A patient with severe sleep apnea featuring constant shallow sleep and sleep fragmentation. **c** The participant with disturbed sleep, though presented a relatively high AP, suffered from excessive sleep depth fluctuation. REM Rapid eye movement, NREM, Non-rapid eye movement, TST Total sleep time, SE Sleep efficiency, AHI Apnea Hypopnea Index, AUC, Area under the sleep depth index curve, AP Proportion of area under the sleep depth index curve.

## Discussion

In this study, we developed and externally validated a deep-learning method for end-to-end annotation of the sleep depth index using a large scale of 11485 PSG recordings. We first viewed the basic properties of the sleep depth index in the second part of the results, the distribution of SDI and its relations to sleep staging. Then in the next part, we checked the correlation between the SDI and the arousal event, which is an indispensable element when researching the sleep fragmentation problem. In the fourth part, we investigated the specific cases showing that SDI would be better than sleep staging in capturing certain nuanced sleep patterns. Finally, in the last section of results, a range of comparisons were made to validate that digital biomarkers extracted from the whole-night SDI had the potential to promote clustering and that different subtypes were associated with significantly varied health conditions and outcomes.

There were some trends of SDI that showcased intuitive findings with respect to the sleep stages. For instance, SDIs in the W and N1 stages were generally small and those in the N3 stages were significantly large. The difference in SDI for epochs in the N2 stage varied drastically, and sometimes the boundary between N1/N2 and N2/N3 was not apparent but the SDIs were close. Unlike traditional sleep staging, which assigns five coarse-grained classes to the sleep state, the proposed sleep depth index offers a more nuanced description of sleep structure, capturing varied patterns of physiological waveform that are not discernible through conventional sleep staging, as shown in Fig. [2](/articles/s41746-025-01607-0#Fig2). This variability of sleep depth index is meaningful as it reflects the intricate transitions in sleep states, as demonstrated in our case studies. Given the distinctiveness of the REM stage[37](#ref-CR37 "Ferini-Strambi, L. & Zucconi, M. Rem sleep behavior disorder. Clin. Neurophysiol. 111, S136–S140 (2000)."),[38](#ref-CR38 "Postuma, R., Gagnon, J.-F., Rompre, S. & Montplaisir, J. Severity of rem atonia loss in idiopathic rem sleep behavior disorder predicts parkinson disease. Neurology 74, 239–244 (2010)."),[39](/articles/s41746-025-01607-0#ref-CR39 "McCarter, S. J., St. Louis, E. K. & Boeve, B. F. Rem sleep behavior disorder and rem sleep without atonia as an early manifestation of degenerative neurological disease. Curr. Neurol. Neurosci. Rep. 12, 182–192 (2012)."), we integrated sleep depth annotation with REM stage classification, producing comprehensive sleep profiling. The predicted REM would also serve as a supplement to feature engineering in addition to the SDI. The proposed SDI was not purposed to replace the sleep stages completely but acted as a valuable source for sleep clinicians to use.

In sleep medicine, arousal indicates a transition from deep to light sleep, making it a suitable candidate for measuring sleep depth. Our experiments showed that a decrease in the sleep depth index strongly correlated with an increase in the duration of arousal, suggesting its potential for monitoring sleep disturbance. More importantly, the arousal event was routinely labeled by experienced clinicians in a cumbersome manner and might suffer from inter-rater variability. As an automatic approach, the proposed method presents a more consistent way than human labeling and adds new insights to measure sleep fragmentation.

Extracting the whole-night SDI for an individual results in a time series rich with information about sleep conditions. Time-domain and Nonlinear features could be directly computed but we could mine more intuitive ones such as AP, which is capable of introducing more nuanced findings than the classic sleep efficiency metric. Based on these digital biomarkers derived from SDI, we performed clustering to obtain two sleep subtypes featuring significant patterns in sleep health. Participants in the identified disturbed subtype were more associated with bad health conditions such as CVD, hypertension, sleep apnea, and insomnia. The disturbed sleep subtype had a higher prevalence of all-cause mortality and fatal coronary heart disease, which offered meaningful indications for clinical practice and relevant prevention. Notably, these are not all the digital biomarkers we can extract. We then envision that more subsequent studies could be conducted to investigate the effects of various time-series features that are able to be explored by the sleep depth index, thus yielding more novel digital biomarkers for sleep medicine. These digital biomarkers would not totally make the traditional sleep metrics such as TST and SE displaced but would help to explore more sleep patterns that were previously overlooked.

Although the concept of sleep depth is frequently discussed in both public and clinical contexts, there are no widely accepted quantitative measurements for sleep depth. Traditional sleep medicine primarily considers the N3 stage as deep sleep[43](/articles/s41746-025-01607-0#ref-CR43 "Wolpert, E. A. A manual of standardized terminology, techniques and scoring system for sleep stages of human subjects. Arch. Gen. Psychiatry 20, 246–247 (1969).") but a single discrete class is far from enough to precisely reflect a high degree of sleep depth. Recently, the ORP[23](/articles/s41746-025-01607-0#ref-CR23 "Younes, M. et al. Odds ratio product of sleep eeg as a continuous measure of sleep state. Sleep 38, 641–654 (2015).") index had demonstrated utility in clinical applications[24](#ref-CR24 "Meza-Vargas, S., Giannouli, E. & Younes, M. Enhancements to the multiple sleep latency test. Nat. Sci. Sleep 8, 145–158 (2016)."),[25](#ref-CR25 "Qanash, S., Giannouli, E. & Younes, M. Assessment of intervention-related changes in non-rapid-eye-movement sleep depth: importance of sleep depth changes within stage 2. Sleep. Med. 40, 84–93 (2017)."),[26](#ref-CR26 "Younes, M., Soiferman, M., Thompson, W. & Giannouli, E. Performance of a new portable wireless sleep monitor. J. Clin. Sleep. Med. 13, 245–258 (2017)."),[27](#ref-CR27 "Younes, M., Azarbarzin, A., Reid, M., Mazzotti, D. R. & Redline, S. Characteristics and reproducibility of novel sleep eeg biomarkers and their variation with sleep apnea and insomnia in a large community-based cohort. Sleep 44, zsab145 (2021)."),[28](/articles/s41746-025-01607-0#ref-CR28 "Younes, M. et al. Sleep architecture based on sleep depth and propensity: patterns in different demographics and sleep disorders and association with health outcomes. Sleep 45, zsac059 (2022)."), but it relied solely on EEG and required manual computations by experts, limiting its efficiency and accessibility. Moreover, the method was not open-sourced mainly due to the unavailability of the reference table to rank the EEG power values, hindering the research community from conducting related research. Consequently, based on the abundant off-the-shelf sleep staging labels, we proposed to use deep learning, with its extraordinary performance in clinical medicine[44](#ref-CR44 "Singhal, K. et al. Large language models encode clinical knowledge. Nature 620, 172–180 (2023)."),[45](#ref-CR45 "De Fauw, J. et al. Clinically applicable deep learning for diagnosis and referral in retinal disease. Nat. Med. 24, 1342–1350 (2018)."),[46](#ref-CR46 "Van der Laak, J., Litjens, G. & Ciompi, F. Deep learning in histopathology: the path to the clinic. Nat. Med. 27, 775–784 (2021)."),[47](#ref-CR47 "Courtiol, P. et al. Deep learning-based classification of mesothelioma improves prediction of patient outcome. Nat. Med. 25, 1519–1525 (2019)."),[48](#ref-CR48 "Ardila, D. et al. End-to-end lung cancer screening with three-dimensional deep learning on low-dose chest computed tomography. Nat. Med. 25, 954–961 (2019)."),[49](/articles/s41746-025-01607-0#ref-CR49 "Liu, Y. et al. A deep learning system for differential diagnosis of skin diseases. Nat. Med. 26, 900–908 (2020)."), for annotating the sleep depth index on large-scale PSG in an end-to-end way. Nevertheless, the native sleep staging labels are coarse-grained and discrete in five classes, prohibiting direct supervised training. To tackle this, we designed a pairwise ranking loss to effectively learn the ordinal relations between stages and take the uncertainty of the relation between the REM stage and other NREM stages into account, making it the first attempt to produce a continuous sleep depth measure from sleep staging labels. The model was based on the Transformer structure[50](/articles/s41746-025-01607-0#ref-CR50 "Vaswani, A. et al. Attention is all you need. Adv. Neural Inform. process. syst. 30, 6000–6010 (2017)."), which is most famous for its scalability of training large-scale neural networks that might show emerging abilities[51](#ref-CR51 "Kaplan, J. et al. Scaling laws for neural language models. arXiv preprint arXiv:2001.08361 (2020)."),[52](#ref-CR52 "Dosovitskiy, A. et al. An image is worth 16x16 words: transformers for image recognition at scale. (ICLR, 2021)."),[53](/articles/s41746-025-01607-0#ref-CR53 "Yang, C., Westover, M. & Sun, J. Biot: Biosignal transformer for cross-data learning in the wild. Adv. Neural Inform. Process. Syst. 36, 78240–78260 (2024)."). We envision that our proposed method of annotating SDI would add new insights into clinicians’ interpretations of the PSG besides the traditional sleep analyses. It could be an important quantitative measurement of sleep depth as it is automatically output by the machine learning model instead of human labeling which might suffer from inter-rater inconsistency.

An easy-to-use web application for automatic annotation of the sleep depth index was deployed online for the evaluation of the polysomnography data. The demonstration is shown in Supplementary Fig. [3](/articles/s41746-025-01607-0#MOESM1). Users can upload EDF files with labeled channel names to obtain analysis results and visualizations. We are continuously enhancing this application to offer more features.

A limitation of our method is its reliance on four PSG channels (EEG, EMG, EOG, and ECG). Future studies should investigate whether similar performance can be achieved with fewer channels, making the approach more feasible in remote and underserved areas where full PSG monitoring is not available. Previous research has shown the effectiveness of using fewer physiological signals in wearable devices for sleep staging[54](/articles/s41746-025-01607-0#ref-CR54 "Boe, A. J. et al. Automating sleep stage classification using wireless, wearable sensors. NPJ Digital Med. 2, 131 (2019)."),[55](/articles/s41746-025-01607-0#ref-CR55 "Radha, M. et al. A deep transfer learning approach for wearable sleep stage classification with photoplethysmography. NPJ Digital Med. 4, 135 (2021)."), suggesting the potential for portable sleep depth annotation systems. Although we have mentioned that a better sleep state can be explored in full PSG monitoring, wearable devices may be a good trade-off in certain medical scenarios. The other issue with the proposed method is that we only include a single channel of EEG, EMG, EOG, and ECG in modeling, thus a question comes out as to whether the performance would be further improved by incorporating more channels or taking the respiratory signals into consideration. Moreover, the model could be tested on a larger dataset with an increasing number of parameters to further verify its scalability. Our current model used a 30-s scale for annotation, based on available sleep staging labels. Higher resolutions could be achieved by modifying model structures and loss functions[56](/articles/s41746-025-01607-0#ref-CR56 "Perslev, M. et al. U-sleep: resilient high-frequency sleep staging. NPJ Digital Med. 4, 72 (2021)."),[57](/articles/s41746-025-01607-0#ref-CR57 "Perslev, M. et al. Automatic detection of abnormal sleeping patterns in stroke patients using high-frequency sleep staging. J. Sleep Res. 31 (2022)."), which is a direction for future research.

In summary, our study underscored the potential of the proposed sleep depth index annotation method as a valuable ancillary tool in clinical sleep medicine. The resultant sleep depth index promises several utilities in real clinic practice and can be explored to yield novel digital biomarkers for sleep health. We hope this work will inspire further research into AI’s role in sleep depth annotation and its significance in sleep medicine.

## Methods

### Dataset and preprocessing

Four large-scale cohorts were used in this study. From the NSRR website[58](/articles/s41746-025-01607-0#ref-CR58 "Zhang, G.-Q. et al. The national sleep research resource: towards a sleep data commons. J. Am. Med. Inform. Assoc. 25, 1351–1358 (2018)."), the Sleep Heart Health Study (SHHS) is a multi-center cohort study implemented by the National Heart Lung & Blood Institute to determine the cardiovascular and other consequences of sleep-disordered breathing[59](/articles/s41746-025-01607-0#ref-CR59 "Quan, S. F. et al. The sleep heart health study: design, rationale, and methods. Sleep 20, 1077–1085 (1997)."). The Cleveland Family Study (CFS) is the largest family-based study of sleep apnea worldwide, which was begun in 1990 with the initial aims of quantifying the familial aggregation of sleep apnea[60](/articles/s41746-025-01607-0#ref-CR60 "Redline, S. et al. The familial aggregation of obstructive sleep apnea. Am. J. Respir. Crit. Care Med. 151, 682–687 (1995)."). Multi-Ethnic Study of Atherosclerosis (MESA) is an NHLBI-sponsored 6-center collaborative longitudinal investigation of factors associated with the development of subclinical cardiovascular disease and the progression of subclinical to clinical cardiovascular disease[61](/articles/s41746-025-01607-0#ref-CR61 "Chen, X. et al. Racial/ethnic differences in sleep disturbances: the multi-ethnic study of atherosclerosis (mesa). Sleep 38, 877–888 (2015)."). MrOS is an ancillary study of the parent Osteoporotic Fractures in Men Study[62](/articles/s41746-025-01607-0#ref-CR62 "Blackwell, T. et al. Associations between sleep architecture and sleep-disordered breathing and cognition in older community-dwelling men: the osteoporotic fractures in men sleep study. J. Am. Geriatr. Soc. 59, 2217–2225 (2011)."). For the SHHS and MROS cohorts, we used records belonging to visit-1. The basic statistics are shown in Supplementary Table [2](/articles/s41746-025-01607-0#MOESM1). We used the MNE library[63](/articles/s41746-025-01607-0#ref-CR63 "Gramfort, A. et al. Meg and eeg data analysis with mne-python. Front. Neurosci. 7, 70133 (2013).") to extract the PSG signals from the raw files and resample them to 100 Hz for concordance. The signals were then trunked to 30-second epochs and saved with the corresponding sleep staging labels and arousal annotation. We chose one EEG (C4) channel, one EMG (chin), one EOR (right eye), and one channel of ECG. We split training sets and internal testing sets for the CFS, MESA, and MROS cohorts by a 7:3 ratio. The SHHS cohort was left as the external validation dataset.

### Definitions of sleep apnea, sleep quality, insomnia, and mortality events

For the four datasets, Apnea-hypopnea index (AHI) values, computed as (All apneas + hypopneas with ≥30% nasal cannula \[or alternative sensor\] reduction with ≥4% oxygen desaturation) / hour of sleep, were extracted from the data harmonized by the NSRR team. Then sleep apnea was defined as AHI ≥5. At the time of these PSG studies, subjects were required to complete some morning surveys with respect to their last night’s sleep. Note that there are some surveys inquiring about the sleep habits of the participants but we did not use them since we concentrated on the immediate sleep feeling after the PSG studies. In our experiment, three variables *diffa10, ltdp10, rest10* were selected for the SHHS dataset. Specifically, the *diffa10* variable measured the difficulty of falling asleep, with 0 indicating No and 1 indicating Yes. Thus participants with *diffa10* being 0 were defined as having insomnia disorders. The *ltdp10* variable measured the quality of sleep in terms of light or deep sleep, with five degrees where a value of 1 indicated light sleep and a value of 5 indicated deep sleep. The *rest10* variable measured the quality of sleep in terms of restless or restful, with five degrees where a value of 1 indicated restless sleep and a value of 5 indicated restful sleep. We selected degree 1/2 and degree 4/5 of each index to compare the results. Participants with both the *ltdp10* and *rest10* being less than 2 were defined as having poor sleep quality and those with both the *ltdp10* and *rest10* being larger than 4 were defined as having good sleep quality. As for the CFS dataset, we extracted four variables *easlp, difbak, slpqua, desslp*. The *easlp* variable measured how easy is it for the subject to fall asleep last night, which was rated on a scale of 1–6, with 1 being very easy and 6 being not at all easy. The *difbak* variable indicated the difficulty of falling back to sleep, with value 0 showing No and value 1 showing Yes. CFS participants with *easlp* less equal to 3 and *difbak* being 0 were defined as not having insomnia and those with *easlp* more than 4 and *difbak* being 1 were defined as having the insomnia symptom. The *slpqua* variable measured the subjects’ feeling of the overall quality of sleep last night, which was rated on a scale of 1–6, with 1 being extremely refreshing and 6 being not refreshing. The *desslp* variable was about the participants’ description of sleep last night, with the value 1 being excellent, 2 being very good, 3 being fair and 4 being poor. Then, participants with *slpqua* being less than 3 and *desslp* less than 2 were defined as having good sleep quality, and those with *slpqua* being more than 4 and *desslp* being more than 3 were defined as having poor sleep quality. As for the MROS dataset, three variables *poxfall, poxqual1, poxqual3* were selected. The *poxfall* variable was a numeric index measuring how long it took for the participant to fall asleep at bedtime last night. MROS participants with *poxfall* more than 40 min were defined as having the insomnia symptom. The *poxqual1* variable inquired about the participants’ feelings about the sleep being light or deep, with five degrees similar to the *ltdp10* variable of the SHHS dataset. The *poxqual3* measured the feelings about the sleep being restless or restful, with five degrees similar to *rest10* in SHHS. MROS participants with both *poxqual1* and *poxqual3* being less than 2 were defined as having poor sleep quality and those with both *poxqual1* and *poxqual3* being larger than 4 were defined as having good sleep quality. Participant deaths in the SHHS cohort, which were identified and confirmed using multiple concurrent approaches including follow-up interviews, written annual questionnaires, telephone contacts, and so on[64](/articles/s41746-025-01607-0#ref-CR64 "Punjabi, N. M. et al. Sleep-disordered breathing and mortality: a prospective cohort study. PLoS Med. 6, e1000132 (2009)."), were sourced from the NSRR dataset. The fatal coronary heart disease was recorded in parent studies datasets at the NSRR website. The censoring time (days to most recent contact or death) was also extracted accordingly.

### Definitions of digital sleep biomarkers

We extracted digital biomarkers from the whole-night sleep depth index from the time domain and the non-linear perspective. As for the time domain, the coefficient of variation and skewness were investigated. Specifically for SDI-featured ones, a ratio below 0.2 (RB, the ratio of sleep depth index less than 0.2), and the proportion of area to the total sleep time (AP) were extracted. As for non-linear features, approximate entropy and detrended fluctuation analysis were used. Approximate entropy is a technique used to quantify the amount of regularity and the unpredictability of fluctuations over time-series data. Smaller values indicate that the data is more regular and predictable[65](/articles/s41746-025-01607-0#ref-CR65 "Richman, J. S. & Moorman, J. R. Physiological time-series analysis using approximate entropy and sample entropy. Am. J. Physiol. Heart Circ. Physiol. 278, H2039–H2049 (2000)."). The detrended fluctuation analysis is a method for determining the statistical self-affinity of a signal, which has been widely used in the physiological domain[66](/articles/s41746-025-01607-0#ref-CR66 "Hardstone, R. et al. Detrended fluctuation analysis: a scale-free view on neuronal oscillations. Front. Physiol. 3, 450 (2012).").

### Statistical analysis

Two-sided t-tests were conducted on the between-group differences of the two clustered subtypes in demographic features, traditional metrics, and digital biomarkers from the SDI. Cohen’s d was used as a measurement of the effect size. Chi-squared tests were utilized to compare the between-group differences for the sex feature, with the odds ratio used to measure the effect size. For the health outcomes, the odds ratio was computed by a Logistic model adjusting for age, sex, BMI, SE, and SL. Bootstrapping was implemented to compute the 95% confidence intervals for the estimates. The log-rank test was used to compare the between-group differences in the survival probability for the two subtypes. The Cox regression model was used to compute the hazard ratios, adjusted for age, sex, BMI, SE, and SL.

### Model structure

An overview of the model is depicted in Supplementary Fig. [4](/articles/s41746-025-01607-0#MOESM1). First, the raw input PSG was segmented into a sequence of patches. Specifically, we had an input PSG epoch \\(x\\in {{\\mathbb{R}}}^{C\\times L}\\), where *C* was the number of physiological channels and *L* was the sequence length. In our study, data from four channels were collected in 30-s epochs at a sampling frequency of 100 Hz for predicting sleep states, thus *C* was 4 and *L* was 3000. The sequence of each channel was first split into *N**c* fixed-size patches with patch size *P* (*N**c* = *L*/*P*). Then the patches from different channels were flattened, yielding a 1D vector composed of *N* = *C* × *N**c* patches. The flattened patch vector was projected to *D* dimensions through a trainable linear projection. The outputs of this projection were conventionally referred to as patch embeddings. Following ideas of the original Vision Transformer (ViT) architecture[52](/articles/s41746-025-01607-0#ref-CR52 "Dosovitskiy, A. et al. An image is worth 16x16 words: transformers for image recognition at scale. (ICLR, 2021)."), learnable and randomly initialized positional embeddings were added to the projected patch embeddings to provide the model with information about the position of the patches in the PSG. In addition, we added the channel embeddings since for the PSG every channel has the signal modality varying dramatically and recent works have shown the necessity to take this into consideration[53](/articles/s41746-025-01607-0#ref-CR53 "Yang, C., Westover, M. & Sun, J. Biot: Biosignal transformer for cross-data learning in the wild. Adv. Neural Inform. Process. Syst. 36, 78240–78260 (2024)."),[67](/articles/s41746-025-01607-0#ref-CR67 "Bao, Y., Sivanandan, S. & Karaletsos, T. Channel vision transformers: an image is worth 1x16x16 words. (ICLR, 2024)."). We then prepended a learnable *CLS* token to the patch embeddings to represent the global contextual information learned by the model. The final embedding vectors then served as input of the standard Transformer encoder which consisted of alternating layers of multihead self-attention (MSA) and (multilayer perception) MLP blocks[50](/articles/s41746-025-01607-0#ref-CR50 "Vaswani, A. et al. Attention is all you need. Adv. Neural Inform. process. syst. 30, 6000–6010 (2017)."), where LayerNorm (LN)[68](/articles/s41746-025-01607-0#ref-CR68 "Ba, J. L. Layer normalization. arXiv preprint arXiv:1607.06450 (2016).") was applied before every block, and residual connections[69](/articles/s41746-025-01607-0#ref-CR69 "He, K., Zhang, X., Ren, S. & Sun, J. Deep residual learning for image recognition. Proc. IEEE conference on computer vision and pattern recognition 770–778 (Institute of Electrical and Electronics Engineers, 2016).") after every block. The standard self-attention mechanism allowed the model to weigh the importance of different patches relative to each other. With *Q*, *K*, *V* being the query, key, and value matrices linearly projected from the input embedding vector \\(X\\in {{\\mathbb{R}}}^{N\\times D}\\),

$$\[Q,K,V\]=X{U}\_{qkv},\\quad {U}\_{qkv}\\in {{\\mathbb{R}}}^{D\\times 3{D}\_{h}}$$

(1)

the attention scores were computed as follows:

$$A=Attention(Q,K,V)=softmax\\left(\\frac{Q{K}^{T}}{\\sqrt{{D}\_{h}}}V\\right)$$

(2)

where *A**i**j* was computed based on the respective *Q**i* and *K**j* representations and *D**h* was computed as *D*/*m* with *m* being the number of heads for multihead self-attention. Specifically as for the multihead self-attention, it was an extension of the native self-attention in which *m* self-attention operations (heads) are conducted. Then these outputs were concatenated and projected to the *D* dimension

$$MSA(X)=\[{A}\_{1}(X);{A}\_{2}(X);...;{A}\_{k}(X)\]{U}\_{msa},\\quad {U}\_{msa}\\in {{\\mathbb{R}}}^{m\\cdot {D}\_{h}\\times D}$$

(3)

The MLP block consisted of two linear layers with a GELU non-linearity. So the *l*th encoder function could be written as

$${X}\_{l}^{{\\prime} }=MSA({Layer}\\,{Norm}({X}\_{l-1}))+{X}\_{l-1},\\quad l=1...{L}\_{T}$$

(4)

$$Encoder({X}\_{l})=MLP({Layer}\\,{Norm}({X}\_{l}^{{\\prime} }))+{X}\_{l}^{{\\prime} },\\quad l=1...{L}\_{T}$$

(5)

where *L**T* was the number of layers of the Transformer encoder. In this study, patch size was set to 100, projection dimension *D* to 512, encoder depth to 6, heads number to 8, and MLP dimension to 2048. After passing through the transformer block, the encoded *CLS* embedding was separately fed into a MLP for predicting the sleep depth and another MLP for predicting the REM stage, both of which resembled the Transformer’s MLP block. The outputs of the sleep depth MLP were scalars with continuous values annotating the sleep depth, and the outputs from the REM MLP were vectors in length of 2 classifying whether the input epoch represented a REM stage. Note that during training the outputs of the depth head were not bounded and we post-processed them with a Sigmoid function to make them have values ranging between 0 and 1. The reason why we did not bound the range in the depth head was that we observed better results obtained in this experiment setting. The pair rank loss and cross-entropy loss were computed on the sleep depth annotation and REM binary classification respectively with details in the following section.

As for the hyperparameter choices, the patch size of 100 was chosen based on the fact that the majority of wave patterns (e.g., K-complex, sleep spindles) lasts about 0.5–2s and the sampling rate is 100 Hz so that the model is capable of capturing enough features. The projection dimension, encoder depth, number of heads, and other hyperparameters were determined mainly in light of previous relevant studies. In our preliminary experiments, we also found no significant changes in the model’s performance in reflecting the clinical indication.

### Loss function

For the design of the loss function for sleep depth annotation, we aimed to leverage the ordinal relationships between different sleep stages, while accounting for uncertain relationships between specific sleep stages. Given a batch of predicted sleep depths ***p*** = \[*p*1, *p*2, …, *p**n*\] and corresponding true labels **y** = \[*y*1, *y*2, …, *y**n*\], the goal was to minimize the loss that considered the margin between different pairs of sleep stages and penalizing the for incorrect ordinal relations. Let \\({\\mathcal{M}}\\) be the mapping from pair types to margins. For a pair of sleep stages (*i*, *j*), the margin was denoted by \\({{\\mathcal{M}}}\_{ij}\\) and computed as:

$${{\\mathcal{M}}}\_{ij}=\\left\\{\\begin{array}{ll}1\\quad &\\,\\text{if}\\,\\,(i,j)=(0,1)\\,\\text{or}\\,(i,j)=(1,0),\\\\ 0.5\\quad &\\,\\text{if}\\,\\,(i,j)=(1,2)\\,\\text{or}\\,(i,j)=(2,1),\\\\ 1.5\\quad &\\,\\text{if}\\,\\,(i,j)=(2,3)\\,\\text{or}\\,(i,j)=(3,2),\\\\ 1.2\\quad &\\,\\text{if}\\,\\,(i,j)=(0,4)\\,\\text{or}\\,(i,j)=(4,0),\\end{array}\\right.$$

(6)

**y** ∈ {0, 1, 2, 3, 4}*n* was the true sleep stage label for the batch of samples, where 0/1/2/3/4 corresponded to W/N1/N2/N3/R. The set of uncertain relationships was denoted by \\({\\mathcal{U}}\\). First, we needed to compute all possible pairs from the predicted depths and true labels, where **p**pairs = {(*p**i*, *p**j*)∣*i* ≠ *j*}**y**pairs = {(*y**i*, *y**j*)∣*i* ≠ *j*} with each pair represented as (*p**i*, *p**j*) and (*y**i*, *y**j*). Second, for each pair of true labels, we retrieved the corresponding margins, \\({{\\mathcal{V}}}\_{ij}={\\mathcal{M}}({y}\_{i},{y}\_{j})\\,\\text{for}\\,({y}\_{i},{y}\_{j})\\in {{\\bf{y}}}\_{{\\rm{pairs}}}\\). In this study, uncertain relationships were identified as \\({\\mathcal{U}}=\\{(1,4),(4,1),(2,4),(4,2),(3,4),(4,3)\\}\\) since we were uncertain about the relation between the REM stage and the other three NREM stages. The mask was formulated as an indicator function as \\({\\mathbb{I}}\[({y}\_{i},{y}\_{j})\\in {\\mathcal{U}}\\,\\text{for}\\,({y}\_{i},{y}\_{j})\\in {{\\bf{y}}}\_{{\\rm{pairs}}}\]\\).

Penalties were computed based on the predicted depths and margins:

$${{\\mathcal{P}}}\_{ij}=\\max (0,{V}\_{{y}\_{i}{y}\_{j}}-\\mathrm{sign}\\,({y}\_{i}-{y}\_{j})({p}\_{i}-{p}\_{j}))$$

(7)

where sign was the sign function. We then computed the final pair rank loss by averaging the penalties, ignoring the uncertain relationships:

$${{\\mathcal{L}}}\_{rank}=\\frac{1}{{\\mathcal{N}}}\\sum \_{(i,j)\\in {{\\bf{y}}}\_{{\\rm{pairs}}}}{{\\mathcal{P}}}\_{ij}\\cdot (1-{\\mathbb{I}}\[({y}\_{i},{y}\_{j})\\in {\\mathcal{U}}\])$$

(8)

, where \\({\\mathcal{N}}={\\sum }\_{(i,j)\\in {{\\bf{y}}}\_{{\\rm{pairs}}}}(1-{\\mathbb{I}}\[({y}\_{i},{y}\_{j})\\in {\\mathcal{U}}\])\\)

On the other side, we used the cross-entropy loss for the REM prediction task. To do this, we need to convert the five-class sleep staging labels to binary labels, we defined \\({y}\_{i}^{\* }={\\mathbb{I}}({y}\_{i}=4)\\), then the cross-entropy loss was:

$${{\\mathcal{L}}}\_{{\\rm{CE}}}=-\\sum \_{i}\[{y}\_{i}^{\* }\\log ({\\hat{y}}\_{i})+(1-{y}\_{i}^{\* })\\log (1-{\\hat{y}}\_{i})\]$$

(9)

where *y**i* was the true label and \\({\\hat{y}}\_{i}\\) was the corresponding predicted probability from the REM classification module. The final loss function for the joint model was formulated as:

$${\\mathcal{L}}={{\\mathcal{L}}}\_{{\\rm{rank}}}+\\alpha {{\\mathcal{L}}}\_{{\\rm{CE}}}$$

(10)

where *α* was a hyperparameter of loss weight. The overall training objective was to minimize the combined loss \\({\\mathcal{L}}\\). In this study, the loss weight *α* was set to 1. The predicted sleep depth index would then be input to a Sigmoid function to make the range between 0 and 1.

### Evaluation metrics

The Pearson correlation coefficient was used to measure the correlation between the decrease in sleep depth and the increase in the duration of arousal. The Spearman’s rank correlation was used to measure the correlation between the sleep depth and the W/N1/N2/N3 sleep stages. The area under the receiver operating characteristic (AUROC) was used to assess the classification performance for REM stage classification. Confidence intervals were computed by Bootstrapping.

## Data availability

The datasets used in this study are available at [https://sleepdata.org/](https://sleepdata.org/).

## Code availability

The source code is available at [https://github.com/sczzz3/SDI](https://github.com/sczzz3/SDI), or [https://github.com/PKUDigitalHealth/SDI](https://github.com/PKUDigitalHealth/SDI).

## References

1.  Tregear, S., Reston, J., Schoelles, K. & Phillips, B. Obstructive sleep apnea and risk of motor vehicle crash: systematic review and meta-analysis. *J. Clin. sleep. Med.* **5**, 573–581 (2009).
    
    [Article](https://doi.org/10.5664%2Fjcsm.27662)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=20465027)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2792976)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Obstructive%20sleep%20apnea%20and%20risk%20of%20motor%20vehicle%20crash%3A%20systematic%20review%20and%20meta-analysis&journal=J.%20Clin.%20sleep.%20Med.&doi=10.5664%2Fjcsm.27662&volume=5&pages=573-581&publication_year=2009&author=Tregear%2CS&author=Reston%2CJ&author=Schoelles%2CK&author=Phillips%2CB) 
    
2.  Smolensky, M. H., Di Milia, L., Ohayon, M. M. & Philip, P. Sleep disorders, medical conditions, and road accident risk. *Accid. Anal. Prev.* **43**, 533–548 (2011).
    
    [Article](https://doi.org/10.1016%2Fj.aap.2009.12.004)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=21130215)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sleep%20disorders%2C%20medical%20conditions%2C%20and%20road%20accident%20risk&journal=Accid.%20Anal.%20Prev.&doi=10.1016%2Fj.aap.2009.12.004&volume=43&pages=533-548&publication_year=2011&author=Smolensky%2CMH&author=Milia%2CL&author=Ohayon%2CMM&author=Philip%2CP) 
    
3.  Iranzo, A. & Santamaria, J. Sleep in neurodegenerative diseases. *Sleep Medicine: A Comprehensive Guide to Its Development, Clinical Milestones, and Advances in Treatment* 271–283 (Springer, 2015).
    
4.  Tsuno, N., Besset, A. & Ritchie, K. et al. Sleep and depression. *J. Clin. psychiatry* **66**, 1254–1269 (2005).
    
    [Article](https://doi.org/10.4088%2FJCP.v66n1008)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=16259539)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sleep%20and%20depression&journal=J.%20Clin.%20psychiatry&doi=10.4088%2FJCP.v66n1008&volume=66&pages=1254-1269&publication_year=2005&author=Tsuno%2CN&author=Besset%2CA&author=Ritchie%2CK) 
    
5.  Martin, S. E., Engleman, H. M., Deary, I. J. & Douglas, N. J. The effect of sleep fragmentation on daytime function. *Am. J. Respir. Crit. Care Med.* **153**, 1328–1332 (1996).
    
    [Article](https://doi.org/10.1164%2Fajrccm.153.4.8616562)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=8616562)  [CAS](/articles/cas-redirect/1:STN:280:DyaK287pslaktw%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20effect%20of%20sleep%20fragmentation%20on%20daytime%20function&journal=Am.%20J.%20Respir.%20Crit.%20Care%20Med.&doi=10.1164%2Fajrccm.153.4.8616562&volume=153&pages=1328-1332&publication_year=1996&author=Martin%2CSE&author=Engleman%2CHM&author=Deary%2CIJ&author=Douglas%2CNJ) 
    
6.  Strollo Jr, P. J. & Rogers, R. M. Obstructive sleep apnea. *N. Engl. J. Med.* **334**, 99–104 (1996).
    
    [Article](https://doi.org/10.1056%2FNEJM199601113340207)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=8531966)  [CAS](/articles/cas-redirect/1:STN:280:DyaK287isl2mug%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Obstructive%20sleep%20apnea&journal=N.%20Engl.%20J.%20Med.&doi=10.1056%2FNEJM199601113340207&volume=334&pages=99-104&publication_year=1996&author=Strollo%20Jr%2CPJ&author=Rogers%2CRM) 
    
7.  Boeve, B. F. Idiopathic rem sleep behaviour disorder in the development of parkinson’s disease. *Lancet Neurol.* **12**, 469–482 (2013).
    
    [Article](https://doi.org/10.1016%2FS1474-4422%2813%2970054-1)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=23578773)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4779953)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Idiopathic%20rem%20sleep%20behaviour%20disorder%20in%20the%20development%20of%20parkinson%E2%80%99s%20disease&journal=Lancet%20Neurol.&doi=10.1016%2FS1474-4422%2813%2970054-1&volume=12&pages=469-482&publication_year=2013&author=Boeve%2CBF) 
    
8.  Stephansen, J. B. et al. Neural network analysis of sleep stages enables efficient diagnosis of narcolepsy. *Nat. Commun.* **9**, 5229 (2018).
    
    [Article](https://doi.org/10.1038%2Fs41467-018-07229-3)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=30523329)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC6283836)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC1cXisVKisLfP)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Neural%20network%20analysis%20of%20sleep%20stages%20enables%20efficient%20diagnosis%20of%20narcolepsy&journal=Nat.%20Commun.&doi=10.1038%2Fs41467-018-07229-3&volume=9&publication_year=2018&author=Stephansen%2CJB) 
    
9.  Bohnen, N. I. & Hu, M. Sleep disturbance as potential risk and progression factor for parkinson’s disease. *J. Parkinson’s. Dis.* **9**, 603–614 (2019).
    
    [Article](https://doi.org/10.3233%2FJPD-191627)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sleep%20disturbance%20as%20potential%20risk%20and%20progression%20factor%20for%20parkinson%E2%80%99s%20disease&journal=J.%20Parkinson%E2%80%99s.%20Dis.&doi=10.3233%2FJPD-191627&volume=9&pages=603-614&publication_year=2019&author=Bohnen%2CNI&author=Hu%2CM) 
    
10.  Berry, R. B. et al. The aasm manual for the scoring of sleep and associated events. *Rules, Terminol. Tech. Specif., Darien, Ill., Am. Acad. Sleep. Med.* **176**, 7 (2012).
    
    [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20aasm%20manual%20for%20the%20scoring%20of%20sleep%20and%20associated%20events&journal=Rules%2C%20Terminol.%20Tech.%20Specif.%2C%20Darien%2C%20Ill.%2C%20Am.%20Acad.%20Sleep.%20Med.&volume=176&publication_year=2012&author=Berry%2CRB) 
    
11.  Magalang, U. J. et al. Agreement in the scoring of respiratory events and sleep among international sleep centers. *Sleep* **36**, 591–596 (2013).
    
    [Article](https://doi.org/10.5665%2Fsleep.2552)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=23565005)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3612261)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Agreement%20in%20the%20scoring%20of%20respiratory%20events%20and%20sleep%20among%20international%20sleep%20centers&journal=Sleep&doi=10.5665%2Fsleep.2552&volume=36&pages=591-596&publication_year=2013&author=Magalang%2CUJ) 
    
12.  Younes, M., Raneri, J. & Hanly, P. Staging sleep in polysomnograms: analysis of inter-scorer variability. *J. Clin. Sleep. Med.* **12**, 885–894 (2016).
    
    [Article](https://doi.org/10.5664%2Fjcsm.5894)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=27070243)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4877322)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Staging%20sleep%20in%20polysomnograms%3A%20analysis%20of%20inter-scorer%20variability&journal=J.%20Clin.%20Sleep.%20Med.&doi=10.5664%2Fjcsm.5894&volume=12&pages=885-894&publication_year=2016&author=Younes%2CM&author=Raneri%2CJ&author=Hanly%2CP) 
    
13.  Biswal, S. et al. Sleepnet: automated sleep staging system via deep learning. arXiv preprint arXiv:1707.08262 (2017).
    
14.  Biswal, S. et al. Expert-level sleep scoring with deep neural networks. *J. Am. Med. Inform. Assoc.* **25**, 1643–1650 (2018).
    
    [Article](https://doi.org/10.1093%2Fjamia%2Focy131)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=30445569)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC6289549)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Expert-level%20sleep%20scoring%20with%20deep%20neural%20networks&journal=J.%20Am.%20Med.%20Inform.%20Assoc.&doi=10.1093%2Fjamia%2Focy131&volume=25&pages=1643-1650&publication_year=2018&author=Biswal%2CS) 
    
15.  Perslev, M., Jensen, M., Darkner, S., Jennum, P. J. & Igel, C. U-time: a fully convolutional network for time series segmentation applied to sleep staging. *Adv. Neural Inform. Processi. Syst.* **32** (2019).
    
16.  Sridhar, N. et al. Deep learning for automated sleep staging using instantaneous heart rate. *NPJ Digital Med.* **3**, 106 (2020).
    
    [Article](https://doi.org/10.1038%2Fs41746-020-0291-x)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning%20for%20automated%20sleep%20staging%20using%20instantaneous%20heart%20rate&journal=NPJ%20Digital%20Med.&doi=10.1038%2Fs41746-020-0291-x&volume=3&publication_year=2020&author=Sridhar%2CN) 
    
17.  Tveit, J. et al. Automated interpretation of clinical electroencephalograms using artificial intelligence. *JAMA Neurol.* **80**, 805–812 (2023).
    
    [Article](https://doi.org/10.1001%2Fjamaneurol.2023.1645)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=37338864)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC10282956)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Automated%20interpretation%20of%20clinical%20electroencephalograms%20using%20artificial%20intelligence&journal=JAMA%20Neurol.&doi=10.1001%2Fjamaneurol.2023.1645&volume=80&pages=805-812&publication_year=2023&author=Tveit%2CJ) 
    
18.  Uchida, S., Maloney, T., March, J., Azari, R. & Feinberg, I. Sigma (12–15 hz) and delta (0.3–3 hz) eeg oscillate reciprocally within nrem sleep. *Brain Res. Bull.* **27**, 93–96 (1991).
    
    [Article](https://doi.org/10.1016%2F0361-9230%2891%2990286-S)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=1933440)  [CAS](/articles/cas-redirect/1:STN:280:DyaK38%2FjsVWlsg%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sigma%20%2812%E2%80%9315%20hz%29%20and%20delta%20%280.3%E2%80%933%20hz%29%20eeg%20oscillate%20reciprocally%20within%20nrem%20sleep&journal=Brain%20Res.%20Bull.&doi=10.1016%2F0361-9230%2891%2990286-S&volume=27&pages=93-96&publication_year=1991&author=Uchida%2CS&author=Maloney%2CT&author=March%2CJ&author=Azari%2CR&author=Feinberg%2CI) 
    
19.  Uchida, S., Maloney, T. & Feinberg, I. Beta (20–28 hz) and delta (0.3–3 hz) eegs oscillate reciprocally across nrem and rem sleep. *Sleep* **15**, 352–358 (1992).
    
    [Article](https://doi.org/10.1093%2Fsleep%2F15.4.352)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=1519011)  [CAS](/articles/cas-redirect/1:STN:280:DyaK38zptVKntA%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Beta%20%2820%E2%80%9328%20hz%29%20and%20delta%20%280.3%E2%80%933%20hz%29%20eegs%20oscillate%20reciprocally%20across%20nrem%20and%20rem%20sleep&journal=Sleep&doi=10.1093%2Fsleep%2F15.4.352&volume=15&pages=352-358&publication_year=1992&author=Uchida%2CS&author=Maloney%2CT&author=Feinberg%2CI) 
    
20.  Bonnet, M. & Arand, D. Heart rate variability: sleep stage, time of night, and arousal influences. *Electroencephalogr. Clin. Neurophysiol.* **102**, 390–396 (1997).
    
    [Article](https://doi.org/10.1016%2FS0921-884X%2896%2996070-1)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=9191582)  [CAS](/articles/cas-redirect/1:STN:280:DyaK2szjsV2itA%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Heart%20rate%20variability%3A%20sleep%20stage%2C%20time%20of%20night%2C%20and%20arousal%20influences&journal=Electroencephalogr.%20Clin.%20Neurophysiol.&doi=10.1016%2FS0921-884X%2896%2996070-1&volume=102&pages=390-396&publication_year=1997&author=Bonnet%2CM&author=Arand%2CD) 
    
21.  Johnson, L., Church, M., Seales, D. & Rossiter, V. Auditory arousal thresholds of good sleepers and poor sleepers with and without flurazepam. *Sleep* **1**, 259–270 (1978).
    
    [Article](https://doi.org/10.1093%2Fsleep%2F1.3.259)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Auditory%20arousal%20thresholds%20of%20good%20sleepers%20and%20poor%20sleepers%20with%20and%20without%20flurazepam&journal=Sleep&doi=10.1093%2Fsleep%2F1.3.259&volume=1&pages=259-270&publication_year=1978&author=Johnson%2CL&author=Church%2CM&author=Seales%2CD&author=Rossiter%2CV) 
    
22.  Gleeson, K., ZWILLlCH, C. W. & White, D. P. The influence of increasing ventilatory effort on arousal from sleep1-3. *Am. Rev. Respir. Dis.* **142**, 295–300 (1990).
    
    [Article](https://doi.org/10.1164%2Fajrccm%2F142.2.295)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=2382892)  [CAS](/articles/cas-redirect/1:STN:280:DyaK3czktlWgtg%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20influence%20of%20increasing%20ventilatory%20effort%20on%20arousal%20from%20sleep1-3&journal=Am.%20Rev.%20Respir.%20Dis.&doi=10.1164%2Fajrccm%2F142.2.295&volume=142&pages=295-300&publication_year=1990&author=Gleeson%2CK&author=ZWILLlCH%2CCW&author=White%2CDP) 
    
23.  Younes, M. et al. Odds ratio product of sleep eeg as a continuous measure of sleep state. *Sleep* **38**, 641–654 (2015).
    
    [Article](https://doi.org/10.5665%2Fsleep.4588)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=25348125)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4355904)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Odds%20ratio%20product%20of%20sleep%20eeg%20as%20a%20continuous%20measure%20of%20sleep%20state&journal=Sleep&doi=10.5665%2Fsleep.4588&volume=38&pages=641-654&publication_year=2015&author=Younes%2CM) 
    
24.  Meza-Vargas, S., Giannouli, E. & Younes, M. Enhancements to the multiple sleep latency test. *Nat. Sci. Sleep* **8**, 145–158 (2016).
    
    [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=27274327)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4869791)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Enhancements%20to%20the%20multiple%20sleep%20latency%20test&journal=Nat.%20Sci.%20Sleep&volume=8&pages=145-158&publication_year=2016&author=Meza-Vargas%2CS&author=Giannouli%2CE&author=Younes%2CM) 
    
25.  Qanash, S., Giannouli, E. & Younes, M. Assessment of intervention-related changes in non-rapid-eye-movement sleep depth: importance of sleep depth changes within stage 2. *Sleep. Med.* **40**, 84–93 (2017).
    
    [Article](https://doi.org/10.1016%2Fj.sleep.2017.09.022)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=29221784)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Assessment%20of%20intervention-related%20changes%20in%20non-rapid-eye-movement%20sleep%20depth%3A%20importance%20of%20sleep%20depth%20changes%20within%20stage%202&journal=Sleep.%20Med.&doi=10.1016%2Fj.sleep.2017.09.022&volume=40&pages=84-93&publication_year=2017&author=Qanash%2CS&author=Giannouli%2CE&author=Younes%2CM) 
    
26.  Younes, M., Soiferman, M., Thompson, W. & Giannouli, E. Performance of a new portable wireless sleep monitor. *J. Clin. Sleep. Med.* **13**, 245–258 (2017).
    
    [Article](https://doi.org/10.5664%2Fjcsm.6456)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=27784419)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC5263080)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Performance%20of%20a%20new%20portable%20wireless%20sleep%20monitor&journal=J.%20Clin.%20Sleep.%20Med.&doi=10.5664%2Fjcsm.6456&volume=13&pages=245-258&publication_year=2017&author=Younes%2CM&author=Soiferman%2CM&author=Thompson%2CW&author=Giannouli%2CE) 
    
27.  Younes, M., Azarbarzin, A., Reid, M., Mazzotti, D. R. & Redline, S. Characteristics and reproducibility of novel sleep eeg biomarkers and their variation with sleep apnea and insomnia in a large community-based cohort. *Sleep* **44**, zsab145 (2021).
    
    [Article](https://doi.org/10.1093%2Fsleep%2Fzsab145)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=34156473)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC8503837)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Characteristics%20and%20reproducibility%20of%20novel%20sleep%20eeg%20biomarkers%20and%20their%20variation%20with%20sleep%20apnea%20and%20insomnia%20in%20a%20large%20community-based%20cohort&journal=Sleep&doi=10.1093%2Fsleep%2Fzsab145&volume=44&publication_year=2021&author=Younes%2CM&author=Azarbarzin%2CA&author=Reid%2CM&author=Mazzotti%2CDR&author=Redline%2CS) 
    
28.  Younes, M. et al. Sleep architecture based on sleep depth and propensity: patterns in different demographics and sleep disorders and association with health outcomes. *Sleep* **45**, zsac059 (2022).
    
    [Article](https://doi.org/10.1093%2Fsleep%2Fzsac059)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=35272350)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC9195236)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sleep%20architecture%20based%20on%20sleep%20depth%20and%20propensity%3A%20patterns%20in%20different%20demographics%20and%20sleep%20disorders%20and%20association%20with%20health%20outcomes&journal=Sleep&doi=10.1093%2Fsleep%2Fzsac059&volume=45&publication_year=2022&author=Younes%2CM) 
    
29.  Metzner, C. et al. Extracting continuous sleep depth from eeg data without machine learning. *Neurobiol. Sleep. Circadian Rhythms* **14**, 100097 (2023).
    
    [Article](https://doi.org/10.1016%2Fj.nbscr.2023.100097)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=37275555)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC10238579)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Extracting%20continuous%20sleep%20depth%20from%20eeg%20data%20without%20machine%20learning&journal=Neurobiol.%20Sleep.%20Circadian%20Rhythms&doi=10.1016%2Fj.nbscr.2023.100097&volume=14&publication_year=2023&author=Metzner%2CC) 
    
30.  LeCun, Y., Bengio, Y. & Hinton, G. Deep learning. *Nature* **521**, 436–444 (2015).
    
    [Article](https://doi.org/10.1038%2Fnature14539)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=26017442)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC2MXht1WlurzP)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning&journal=Nature&doi=10.1038%2Fnature14539&volume=521&pages=436-444&publication_year=2015&author=LeCun%2CY&author=Bengio%2CY&author=Hinton%2CG) 
    
31.  Goldstein, C. A. et al. Artificial intelligence in sleep medicine: an american academy of sleep medicine position statement. *J. Clin. Sleep. Med.* **16**, 605–607 (2020).
    
    [Article](https://doi.org/10.5664%2Fjcsm.8288)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=32022674)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC7161449)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Artificial%20intelligence%20in%20sleep%20medicine%3A%20an%20american%20academy%20of%20sleep%20medicine%20position%20statement&journal=J.%20Clin.%20Sleep.%20Med.&doi=10.5664%2Fjcsm.8288&volume=16&pages=605-607&publication_year=2020&author=Goldstein%2CCA) 
    
32.  Bandyopadhyay, A. & Goldstein, C. Clinical applications of artificial intelligence in sleep medicine: a sleep clinician’s perspective. *Sleep. Breath.* **27**, 39–55 (2023).
    
    [Article](https://link.springer.com/doi/10.1007/s11325-022-02592-4)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=35262853)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Clinical%20applications%20of%20artificial%20intelligence%20in%20sleep%20medicine%3A%20a%20sleep%20clinician%E2%80%99s%20perspective&journal=Sleep.%20Breath.&doi=10.1007%2Fs11325-022-02592-4&volume=27&pages=39-55&publication_year=2023&author=Bandyopadhyay%2CA&author=Goldstein%2CC) 
    
33.  Liu, T.-Y. et al. Learning to rank for information retrieval. *Found. Trends® Inf. Retr.* **3**, 225–331 (2009).
    
    [Article](https://doi.org/10.1561%2F1500000016)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC3cXhtlSmu7o%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Learning%20to%20rank%20for%20information%20retrieval&journal=Found.%20Trends%C2%AE%20Inf.%20Retr.&doi=10.1561%2F1500000016&volume=3&pages=225-331&publication_year=2009&author=Liu%2CT-Y) 
    
34.  Karatzoglou, A., Baltrunas, L. & Shi, Y. Learning to rank for recommender systems. *Proce. 7th ACM Conference on Recommender Systems* 493–494 (Association for Computing Machinery, 2013).
    
35.  Agarwal, A. et al. Learning to rank for robust question answering. *Proc. 21st ACM international conference on Information and knowledge management* 833–842 (Association for Computing Machinery, 2012).
    
36.  Patel, A. K., Reddy, V., Shumway, K. R. & Araujo, J. F. Physiology, sleep stages. In StatPearls \[Internet\] (StatPearls Publishing, 2022).
    
37.  Ferini-Strambi, L. & Zucconi, M. Rem sleep behavior disorder. *Clin. Neurophysiol.* **111**, S136–S140 (2000).
    
    [Article](https://doi.org/10.1016%2FS1388-2457%2800%2900414-4)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=10996567)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Rem%20sleep%20behavior%20disorder&journal=Clin.%20Neurophysiol.&doi=10.1016%2FS1388-2457%2800%2900414-4&volume=111&pages=S136-S140&publication_year=2000&author=Ferini-Strambi%2CL&author=Zucconi%2CM) 
    
38.  Postuma, R., Gagnon, J.-F., Rompre, S. & Montplaisir, J. Severity of rem atonia loss in idiopathic rem sleep behavior disorder predicts parkinson disease. *Neurology* **74**, 239–244 (2010).
    
    [Article](https://doi.org/10.1212%2FWNL.0b013e3181ca0166)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=20083800)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2872606)  [CAS](/articles/cas-redirect/1:STN:280:DC%2BC3c%2Fjtlerug%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Severity%20of%20rem%20atonia%20loss%20in%20idiopathic%20rem%20sleep%20behavior%20disorder%20predicts%20parkinson%20disease&journal=Neurology&doi=10.1212%2FWNL.0b013e3181ca0166&volume=74&pages=239-244&publication_year=2010&author=Postuma%2CR&author=Gagnon%2CJ-F&author=Rompre%2CS&author=Montplaisir%2CJ) 
    
39.  McCarter, S. J., St. Louis, E. K. & Boeve, B. F. Rem sleep behavior disorder and rem sleep without atonia as an early manifestation of degenerative neurological disease. *Curr. Neurol. Neurosci. Rep.* **12**, 182–192 (2012).
    
    [Article](https://link.springer.com/doi/10.1007/s11910-012-0253-z)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=22328094)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3656587)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC38Xkt1Cjsrg%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Rem%20sleep%20behavior%20disorder%20and%20rem%20sleep%20without%20atonia%20as%20an%20early%20manifestation%20of%20degenerative%20neurological%20disease&journal=Curr.%20Neurol.%20Neurosci.%20Rep.&doi=10.1007%2Fs11910-012-0253-z&volume=12&pages=182-192&publication_year=2012&author=McCarter%2CSJ&author=Louis%2CEK&author=Boeve%2CBF) 
    
40.  Scammell, T. E., Arrigoni, E. & Lipton, J. O. Neural circuitry of wakefulness and sleep. *Neuron* **93**, 747–765 (2017).
    
    [Article](https://doi.org/10.1016%2Fj.neuron.2017.01.014)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=28231463)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC5325713)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC2sXjsVGgtbg%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Neural%20circuitry%20of%20wakefulness%20and%20sleep&journal=Neuron&doi=10.1016%2Fj.neuron.2017.01.014&volume=93&pages=747-765&publication_year=2017&author=Scammell%2CTE&author=Arrigoni%2CE&author=Lipton%2CJO) 
    
41.  Kleiger, R. E., Miller, J. P., Bigger Jr, J. T. & Moss, A. J. Decreased heart rate variability and its association with increased mortality after acute myocardial infarction. *Am. J. Cardiol.* **59**, 256–262 (1987).
    
    [Article](https://doi.org/10.1016%2F0002-9149%2887%2990795-8)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=3812275)  [CAS](/articles/cas-redirect/1:STN:280:DyaL2s7isVGisw%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Decreased%20heart%20rate%20variability%20and%20its%20association%20with%20increased%20mortality%20after%20acute%20myocardial%20infarction&journal=Am.%20J.%20Cardiol.&doi=10.1016%2F0002-9149%2887%2990795-8&volume=59&pages=256-262&publication_year=1987&author=Kleiger%2CRE&author=Miller%2CJP&author=Bigger%20Jr%2CJT&author=Moss%2CAJ) 
    
42.  Bigger Jr, J. T. et al. Frequency domain measures of heart period variability and mortality after myocardial infarction. *Circulation* **85**, 164–171 (1992).
    
    [Article](https://doi.org/10.1161%2F01.CIR.85.1.164)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=1728446)  [CAS](/articles/cas-redirect/1:STN:280:DyaK38%2Fpslahuw%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Frequency%20domain%20measures%20of%20heart%20period%20variability%20and%20mortality%20after%20myocardial%20infarction&journal=Circulation&doi=10.1161%2F01.CIR.85.1.164&volume=85&pages=164-171&publication_year=1992&author=Bigger%20Jr%2CJT) 
    
43.  Wolpert, E. A. A manual of standardized terminology, techniques and scoring system for sleep stages of human subjects. *Arch. Gen. Psychiatry* **20**, 246–247 (1969).
    
    [Article](https://doi.org/10.1001%2Farchpsyc.1969.01740140118016)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20manual%20of%20standardized%20terminology%2C%20techniques%20and%20scoring%20system%20for%20sleep%20stages%20of%20human%20subjects&journal=Arch.%20Gen.%20Psychiatry&doi=10.1001%2Farchpsyc.1969.01740140118016&volume=20&pages=246-247&publication_year=1969&author=Wolpert%2CEA) 
    
44.  Singhal, K. et al. Large language models encode clinical knowledge. *Nature* **620**, 172–180 (2023).
    
    [Article](https://doi.org/10.1038%2Fs41586-023-06291-2)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=37438534)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC10396962)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BB3sXhsVKju7zP)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Large%20language%20models%20encode%20clinical%20knowledge&journal=Nature&doi=10.1038%2Fs41586-023-06291-2&volume=620&pages=172-180&publication_year=2023&author=Singhal%2CK) 
    
45.  De Fauw, J. et al. Clinically applicable deep learning for diagnosis and referral in retinal disease. *Nat. Med.* **24**, 1342–1350 (2018).
    
    [Article](https://doi.org/10.1038%2Fs41591-018-0107-6)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=30104768)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Clinically%20applicable%20deep%20learning%20for%20diagnosis%20and%20referral%20in%20retinal%20disease&journal=Nat.%20Med.&doi=10.1038%2Fs41591-018-0107-6&volume=24&pages=1342-1350&publication_year=2018&author=Fauw%2CJ) 
    
46.  Van der Laak, J., Litjens, G. & Ciompi, F. Deep learning in histopathology: the path to the clinic. *Nat. Med.* **27**, 775–784 (2021).
    
    [Article](https://doi.org/10.1038%2Fs41591-021-01343-4)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=33990804)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning%20in%20histopathology%3A%20the%20path%20to%20the%20clinic&journal=Nat.%20Med.&doi=10.1038%2Fs41591-021-01343-4&volume=27&pages=775-784&publication_year=2021&author=Laak%2CJ&author=Litjens%2CG&author=Ciompi%2CF) 
    
47.  Courtiol, P. et al. Deep learning-based classification of mesothelioma improves prediction of patient outcome. *Nat. Med.* **25**, 1519–1525 (2019).
    
    [Article](https://doi.org/10.1038%2Fs41591-019-0583-3)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=31591589)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC1MXhvFaksbjE)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Deep%20learning-based%20classification%20of%20mesothelioma%20improves%20prediction%20of%20patient%20outcome&journal=Nat.%20Med.&doi=10.1038%2Fs41591-019-0583-3&volume=25&pages=1519-1525&publication_year=2019&author=Courtiol%2CP) 
    
48.  Ardila, D. et al. End-to-end lung cancer screening with three-dimensional deep learning on low-dose chest computed tomography. *Nat. Med.* **25**, 954–961 (2019).
    
    [Article](https://doi.org/10.1038%2Fs41591-019-0447-x)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=31110349)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BC1MXhtVWqurfO)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=End-to-end%20lung%20cancer%20screening%20with%20three-dimensional%20deep%20learning%20on%20low-dose%20chest%20computed%20tomography&journal=Nat.%20Med.&doi=10.1038%2Fs41591-019-0447-x&volume=25&pages=954-961&publication_year=2019&author=Ardila%2CD) 
    
49.  Liu, Y. et al. A deep learning system for differential diagnosis of skin diseases. *Nat. Med.* **26**, 900–908 (2020).
    
    [Article](https://doi.org/10.1038%2Fs41591-020-0842-3)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=32424212)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BB3cXpsFyjs7s%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20deep%20learning%20system%20for%20differential%20diagnosis%20of%20skin%20diseases&journal=Nat.%20Med.&doi=10.1038%2Fs41591-020-0842-3&volume=26&pages=900-908&publication_year=2020&author=Liu%2CY) 
    
50.  Vaswani, A. et al. Attention is all you need. *Adv. Neural Inform. process. syst.* **30**, 6000–6010 (2017).
    
    [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Attention%20is%20all%20you%20need&journal=Adv.%20Neural%20Inform.%20process.%20syst.&volume=30&pages=6000-6010&publication_year=2017&author=Vaswani%2CA) 
    
51.  Kaplan, J. et al. Scaling laws for neural language models. arXiv preprint arXiv:2001.08361 (2020).
    
52.  Dosovitskiy, A. et al. An image is worth 16x16 words: transformers for image recognition at scale. (ICLR, 2021).
    
53.  Yang, C., Westover, M. & Sun, J. Biot: Biosignal transformer for cross-data learning in the wild. *Adv. Neural Inform. Process. Syst.* **36**, 78240–78260 (2024).
    
54.  Boe, A. J. et al. Automating sleep stage classification using wireless, wearable sensors. *NPJ Digital Med.* **2**, 131 (2019).
    
    [Article](https://doi.org/10.1038%2Fs41746-019-0210-1)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Automating%20sleep%20stage%20classification%20using%20wireless%2C%20wearable%20sensors&journal=NPJ%20Digital%20Med.&doi=10.1038%2Fs41746-019-0210-1&volume=2&publication_year=2019&author=Boe%2CAJ) 
    
55.  Radha, M. et al. A deep transfer learning approach for wearable sleep stage classification with photoplethysmography. *NPJ Digital Med.* **4**, 135 (2021).
    
    [Article](https://doi.org/10.1038%2Fs41746-021-00510-8)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=A%20deep%20transfer%20learning%20approach%20for%20wearable%20sleep%20stage%20classification%20with%20photoplethysmography&journal=NPJ%20Digital%20Med.&doi=10.1038%2Fs41746-021-00510-8&volume=4&publication_year=2021&author=Radha%2CM) 
    
56.  Perslev, M. et al. U-sleep: resilient high-frequency sleep staging. *NPJ Digital Med.* **4**, 72 (2021).
    
    [Article](https://doi.org/10.1038%2Fs41746-021-00440-5)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=U-sleep%3A%20resilient%20high-frequency%20sleep%20staging&journal=NPJ%20Digital%20Med.&doi=10.1038%2Fs41746-021-00440-5&volume=4&publication_year=2021&author=Perslev%2CM) 
    
57.  Perslev, M. et al. Automatic detection of abnormal sleeping patterns in stroke patients using high-frequency sleep staging. *J. Sleep Res.* **31** (2022).
    
58.  Zhang, G.-Q. et al. The national sleep research resource: towards a sleep data commons. *J. Am. Med. Inform. Assoc.* **25**, 1351–1358 (2018).
    
    [Article](https://doi.org/10.1093%2Fjamia%2Focy064)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=29860441)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC6188513)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20national%20sleep%20research%20resource%3A%20towards%20a%20sleep%20data%20commons&journal=J.%20Am.%20Med.%20Inform.%20Assoc.&doi=10.1093%2Fjamia%2Focy064&volume=25&pages=1351-1358&publication_year=2018&author=Zhang%2CG-Q) 
    
59.  Quan, S. F. et al. The sleep heart health study: design, rationale, and methods. *Sleep* **20**, 1077–1085 (1997).
    
    [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=9493915)  [CAS](/articles/cas-redirect/1:STN:280:DyaK1c7lt12gtg%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20sleep%20heart%20health%20study%3A%20design%2C%20rationale%2C%20and%20methods&journal=Sleep&volume=20&pages=1077-1085&publication_year=1997&author=Quan%2CSF) 
    
60.  Redline, S. et al. The familial aggregation of obstructive sleep apnea. *Am. J. Respir. Crit. Care Med.* **151**, 682–687 (1995).
    
    [Article](https://doi.org/10.1164%2Fajrccm%2F151.3_Pt_1.682)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=7881656)  [CAS](/articles/cas-redirect/1:STN:280:DyaK2M7oslCitQ%3D%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=The%20familial%20aggregation%20of%20obstructive%20sleep%20apnea&journal=Am.%20J.%20Respir.%20Crit.%20Care%20Med.&doi=10.1164%2Fajrccm%2F151.3_Pt_1.682&volume=151&pages=682-687&publication_year=1995&author=Redline%2CS) 
    
61.  Chen, X. et al. Racial/ethnic differences in sleep disturbances: the multi-ethnic study of atherosclerosis (mesa). *Sleep* **38**, 877–888 (2015).
    
    [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=25409106)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC4434554)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Racial%2Fethnic%20differences%20in%20sleep%20disturbances%3A%20the%20multi-ethnic%20study%20of%20atherosclerosis%20%28mesa%29&journal=Sleep&volume=38&pages=877-888&publication_year=2015&author=Chen%2CX) 
    
62.  Blackwell, T. et al. Associations between sleep architecture and sleep-disordered breathing and cognition in older community-dwelling men: the osteoporotic fractures in men sleep study. *J. Am. Geriatr. Soc.* **59**, 2217–2225 (2011).
    
    [Article](https://doi.org/10.1111%2Fj.1532-5415.2011.03731.x)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=22188071)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3245643)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Associations%20between%20sleep%20architecture%20and%20sleep-disordered%20breathing%20and%20cognition%20in%20older%20community-dwelling%20men%3A%20the%20osteoporotic%20fractures%20in%20men%20sleep%20study&journal=J.%20Am.%20Geriatr.%20Soc.&doi=10.1111%2Fj.1532-5415.2011.03731.x&volume=59&pages=2217-2225&publication_year=2011&author=Blackwell%2CT) 
    
63.  Gramfort, A. et al. Meg and eeg data analysis with mne-python. *Front. Neurosci.* **7**, 70133 (2013).
    
    [Article](https://doi.org/10.3389%2Ffnins.2013.00267)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Meg%20and%20eeg%20data%20analysis%20with%20mne-python&journal=Front.%20Neurosci.&doi=10.3389%2Ffnins.2013.00267&volume=7&publication_year=2013&author=Gramfort%2CA) 
    
64.  Punjabi, N. M. et al. Sleep-disordered breathing and mortality: a prospective cohort study. *PLoS Med.* **6**, e1000132 (2009).
    
    [Article](https://doi.org/10.1371%2Fjournal.pmed.1000132)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=19688045)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2722083)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Sleep-disordered%20breathing%20and%20mortality%3A%20a%20prospective%20cohort%20study&journal=PLoS%20Med.&doi=10.1371%2Fjournal.pmed.1000132&volume=6&publication_year=2009&author=Punjabi%2CNM) 
    
65.  Richman, J. S. & Moorman, J. R. Physiological time-series analysis using approximate entropy and sample entropy. *Am. J. Physiol. Heart Circ. Physiol.* **278**, H2039–H2049 (2000).
    
    [Article](https://doi.org/10.1152%2Fajpheart.2000.278.6.H2039)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=10843903)  [CAS](/articles/cas-redirect/1:CAS:528:DC%2BD3cXks1yms74%3D)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Physiological%20time-series%20analysis%20using%20approximate%20entropy%20and%20sample%20entropy&journal=Am.%20J.%20Physiol.%20Heart%20Circ.%20Physiol.&doi=10.1152%2Fajpheart.2000.278.6.H2039&volume=278&pages=H2039-H2049&publication_year=2000&author=Richman%2CJS&author=Moorman%2CJR) 
    
66.  Hardstone, R. et al. Detrended fluctuation analysis: a scale-free view on neuronal oscillations. *Front. Physiol.* **3**, 450 (2012).
    
    [Article](https://doi.org/10.3389%2Ffphys.2012.00450)  [PubMed](http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&dopt=Abstract&list_uids=23226132)  [PubMed Central](http://www.ncbi.nlm.nih.gov/pmc/articles/PMC3510427)  [Google Scholar](http://scholar.google.com/scholar_lookup?&title=Detrended%20fluctuation%20analysis%3A%20a%20scale-free%20view%20on%20neuronal%20oscillations&journal=Front.%20Physiol.&doi=10.3389%2Ffphys.2012.00450&volume=3&publication_year=2012&author=Hardstone%2CR) 
    
67.  Bao, Y., Sivanandan, S. & Karaletsos, T. Channel vision transformers: an image is worth 1x16x16 words. (ICLR, 2024).
    
68.  Ba, J. L. Layer normalization. arXiv preprint arXiv:1607.06450 (2016).
    
69.  He, K., Zhang, X., Ren, S. & Sun, J. Deep residual learning for image recognition. *Proc. IEEE conference on computer vision and pattern recognition* 770–778 (Institute of Electrical and Electronics Engineers, 2016).
    

[Download references](https://citation-needed.springer.com/v2/references/10.1038/s41746-025-01607-0?format=refman&flavour=references)

## Acknowledgements

This work was supported by the National Natural Science Foundation of China (62102008, 62172018); Clinical Medicine Plus X - Young Scholars Project of Peking University, the Fundamental Research Funds for the Central Universities (PKU2024LCXQ030); PKU-OPPO Fund (B0202301); CCF-Zhipu Large Model Innovation Fund (CCF-Zhipu202414), the Ministry of Science and Technology of the People’s Republic of China (STI2030-Major Projects2021ZD0201900). Dr. Westover’s laboratory received support from grants from the NIH (R01NS102190, R01NS102574, R01NS107291, RF1AG064312, RF1NS120947, R01AG073410, R01HL161253, R01NS126282, R01AG073598) and NSF (2014431).

## Author information

### Authors and Affiliations

1.  National Institute of Health Data Science, Peking University, Beijing, China
    
    Songchi Zhou & Shenda Hong
    
2.  Department of Bioinformatics and Biostatistics, Shanghai Jiao Tong University, Shanghai, China
    
    Ge Song
    
3.  Department of Neurology, Beth Israel Deaconess Medical Center, Harvard Medical School, Boston, MA, USA
    
    Haoqi Sun & M. Brandon Westover
    
4.  HeartVoice Medical Technology, Hefei, China
    
    Deyun Zhang
    
5.  Department of Psychiatry and Behavioral Sciences, University of California, San Francisco, CA, USA
    
    Yue Leng
    

Authors

1.  Songchi Zhou
    
    [View author publications](/search?author=Songchi%20Zhou)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Songchi%20Zhou) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Songchi%20Zhou%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
2.  Ge Song
    
    [View author publications](/search?author=Ge%20Song)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Ge%20Song) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Ge%20Song%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
3.  Haoqi Sun
    
    [View author publications](/search?author=Haoqi%20Sun)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Haoqi%20Sun) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Haoqi%20Sun%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
4.  Deyun Zhang
    
    [View author publications](/search?author=Deyun%20Zhang)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Deyun%20Zhang) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Deyun%20Zhang%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
5.  Yue Leng
    
    [View author publications](/search?author=Yue%20Leng)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Yue%20Leng) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Yue%20Leng%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
6.  M. Brandon Westover
    
    [View author publications](/search?author=M.%20Brandon%20Westover)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=M.%20Brandon%20Westover) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22M.%20Brandon%20Westover%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    
7.  Shenda Hong
    
    [View author publications](/search?author=Shenda%20Hong)
    
    Search author on:[PubMed](https://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=search&term=Shenda%20Hong) [Google Scholar](https://scholar.google.co.uk/scholar?as_q=&num=10&btnG=Search+Scholar&as_epq=&as_oq=&as_eq=&as_occt=any&as_sauthors=%22Shenda%20Hong%22&as_publication=&as_ylo=&as_yhi=&as_allsubj=all&hl=en)
    

### Contributions

S.Z.: conceptualization, data curation, methodology, formal analysis, validation, and manuscript writing. G.S.: data curation, methodology, formal analysis, and manuscript writing. H.S.: conceptualization, formal analysis, validation, and manuscript writing. D.Z.: data curation, software, and validation. Y.L.: conceptualization, validation, manuscript writing, and supervision. M.B.W.: conceptualization, validation, funding acquisition, and supervision. S.H.: conceptualization, methodology, formal analysis, funding acquisition, manuscript writing, and supervision. All authors have read and approved the manuscript.

### Corresponding author

Correspondence to [Shenda Hong](mailto:hongshenda@pku.edu.cn).

## Ethics declarations

### Competing interests

M.B.W. is a co-founder, scientific advisor, consultant to, and has personal equity interest in Beacon Biosignals. The other authors declare no competing interests.

## Additional information

**Publisher’s note** Springer Nature remains neutral with regard to jurisdictional claims in published maps and institutional affiliations.

## Supplementary information

### [Supplemental material (download PDF )](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41746-025-01607-0/MediaObjects/41746_2025_1607_MOESM1_ESM.pdf)

## Rights and permissions

**Open Access** This article is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if you modified the licensed material. You do not have permission under this licence to share adapted material derived from this article or parts of it. The images or other third party material in this article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included in the article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To view a copy of this licence, visit [http://creativecommons.org/licenses/by-nc-nd/4.0/](http://creativecommons.org/licenses/by-nc-nd/4.0/).

[Reprints and permissions](https://s100.copyright.com/AppDispatchServlet?title=Continuous%20sleep%20depth%20index%20annotation%20with%20deep%20learning%20yields%20novel%20digital%20biomarkers%20for%20sleep%20health&author=Songchi%20Zhou%20et%20al&contentID=10.1038%2Fs41746-025-01607-0&copyright=The%20Author%28s%29&publication=2398-6352&publicationDate=2025-04-11&publisherName=SpringerNature&orderBeanReset=true&oa=CC%20BY-NC-ND)

## About this article

[![Check for updates. Verify currency and authenticity via CrossMark](data:image/svg+xml;base64,PHN2ZyBoZWlnaHQ9IjgxIiB3aWR0aD0iNTciIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgZmlsbD0ibm9uZSIgZmlsbC1ydWxlPSJldmVub2RkIj48cGF0aCBkPSJtMTcuMzUgMzUuNDUgMjEuMy0xNC4ydi0xNy4wM2gtMjEuMyIgZmlsbD0iIzk4OTg5OCIvPjxwYXRoIGQ9Im0zOC42NSAzNS40NS0yMS4zLTE0LjJ2LTE3LjAzaDIxLjMiIGZpbGw9IiM3NDc0NzQiLz48cGF0aCBkPSJtMjggLjVjLTEyLjk4IDAtMjMuNSAxMC41Mi0yMy41IDIzLjVzMTAuNTIgMjMuNSAyMy41IDIzLjUgMjMuNS0xMC41MiAyMy41LTIzLjVjMC02LjIzLTIuNDgtMTIuMjEtNi44OC0xNi42Mi00LjQxLTQuNC0xMC4zOS02Ljg4LTE2LjYyLTYuODh6bTAgNDEuMjVjLTkuOCAwLTE3Ljc1LTcuOTUtMTcuNzUtMTcuNzVzNy45NS0xNy43NSAxNy43NS0xNy43NSAxNy43NSA3Ljk1IDE3Ljc1IDE3Ljc1YzAgNC43MS0xLjg3IDkuMjItNS4yIDEyLjU1cy03Ljg0IDUuMi0xMi41NSA1LjJ6IiBmaWxsPSIjNTM1MzUzIi8+PHBhdGggZD0ibTQxIDM2Yy01LjgxIDYuMjMtMTUuMjMgNy40NS0yMi40MyAyLjktNy4yMS00LjU1LTEwLjE2LTEzLjU3LTcuMDMtMjEuNWwtNC45Mi0zLjExYy00Ljk1IDEwLjctMS4xOSAyMy40MiA4Ljc4IDI5LjcxIDkuOTcgNi4zIDIzLjA3IDQuMjIgMzAuNi00Ljg2eiIgZmlsbD0iIzljOWM5YyIvPjxwYXRoIGQ9Im0uMiA1OC40NWMwLS43NS4xMS0xLjQyLjMzLTIuMDFzLjUyLTEuMDkuOTEtMS41Yy4zOC0uNDEuODMtLjczIDEuMzQtLjk0LjUxLS4yMiAxLjA2LS4zMiAxLjY1LS4zMi41NiAwIDEuMDYuMTEgMS41MS4zNS40NC4yMy44MS41IDEuMS44MWwtLjkxIDEuMDFjLS4yNC0uMjQtLjQ5LS40Mi0uNzUtLjU2LS4yNy0uMTMtLjU4LS4yLS45My0uMi0uMzkgMC0uNzMuMDgtMS4wNS4yMy0uMzEuMTYtLjU4LjM3LS44MS42Ni0uMjMuMjgtLjQxLjYzLS41MyAxLjA0LS4xMy40MS0uMTkuODgtLjE5IDEuMzkgMCAxLjA0LjIzIDEuODYuNjggMi40Ni40NS41OSAxLjA2Ljg4IDEuODQuODguNDEgMCAuNzctLjA3IDEuMDctLjIzcy41OS0uMzkuODUtLjY4bC45MSAxYy0uMzguNDMtLjguNzYtMS4yOC45OS0uNDcuMjItMSAuMzQtMS41OC4zNC0uNTkgMC0xLjEzLS4xLTEuNjQtLjMxLS41LS4yLS45NC0uNTEtMS4zMS0uOTEtLjM4LS40LS42Ny0uOS0uODgtMS40OC0uMjItLjU5LS4zMy0xLjI2LS4zMy0yLjAyem04LjQtNS4zM2gxLjYxdjIuNTRsLS4wNSAxLjMzYy4yOS0uMjcuNjEtLjUxLjk2LS43MnMuNzYtLjMxIDEuMjQtLjMxYy43MyAwIDEuMjcuMjMgMS42MS43MS4zMy40Ny41IDEuMTQuNSAyLjAydjQuMzFoLTEuNjF2LTQuMWMwLS41Ny0uMDgtLjk3LS4yNS0xLjIxLS4xNy0uMjMtLjQ1LS4zNS0uODMtLjM1LS4zIDAtLjU2LjA4LS43OS4yMi0uMjMuMTUtLjQ5LjM2LS43OC42NHY0LjhoLTEuNjF6bTcuMzcgNi40NWMwLS41Ni4wOS0xLjA2LjI2LTEuNTEuMTgtLjQ1LjQyLS44My43MS0xLjE0LjI5LS4zLjYzLS41NCAxLjAxLS43MS4zOS0uMTcuNzgtLjI1IDEuMTgtLjI1LjQ3IDAgLjg4LjA4IDEuMjMuMjQuMzYuMTYuNjUuMzguODkuNjdzLjQyLjYzLjU0IDEuMDNjLjEyLjQxLjE4Ljg0LjE4IDEuMzIgMCAuMzItLjAyLjU3LS4wNy43NmgtNC4zNmMuMDcuNjIuMjkgMS4xLjY1IDEuNDQuMzYuMzMuODIuNSAxLjM4LjUuMjkgMCAuNTctLjA0LjgzLS4xM3MuNTEtLjIxLjc2LS4zN2wuNTUgMS4wMWMtLjMzLjIxLS42OS4zOS0xLjA5LjUzLS40MS4xNC0uODMuMjEtMS4yNi4yMS0uNDggMC0uOTItLjA4LTEuMzQtLjI1LS40MS0uMTYtLjc2LS40LTEuMDctLjctLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDQtLjI2LS45NS0uMjYtMS41MnptNC42LS42MmMwLS41NS0uMTEtLjk4LS4zNC0xLjI4LS4yMy0uMzEtLjU4LS40Ny0xLjA2LS40Ny0uNDEgMC0uNzcuMTUtMS4wNy40NS0uMzEuMjktLjUuNzMtLjU4IDEuM3ptMi41LjYyYzAtLjU3LjA5LTEuMDguMjgtMS41My4xOC0uNDQuNDMtLjgyLjc1LTEuMTNzLjY5LS41NCAxLjEtLjcxYy40Mi0uMTYuODUtLjI0IDEuMzEtLjI0LjQ1IDAgLjg0LjA4IDEuMTcuMjNzLjYxLjM0Ljg1LjU3bC0uNzcgMS4wMmMtLjE5LS4xNi0uMzgtLjI4LS41Ni0uMzctLjE5LS4wOS0uMzktLjE0LS42MS0uMTQtLjU2IDAtMS4wMS4yMS0xLjM1LjYzLS4zNS40MS0uNTIuOTctLjUyIDEuNjcgMCAuNjkuMTcgMS4yNC41MSAxLjY2LjM0LjQxLjc4LjYyIDEuMzIuNjIuMjggMCAuNTQtLjA2Ljc4LS4xNy4yNC0uMTIuNDUtLjI2LjY0LS40MmwuNjcgMS4wM2MtLjMzLjI5LS42OS41MS0xLjA4LjY1LS4zOS4xNS0uNzguMjMtMS4xOC4yMy0uNDYgMC0uOS0uMDgtMS4zMS0uMjQtLjQtLjE2LS43NS0uMzktMS4wNS0uN3MtLjUzLS42OS0uNy0xLjEzYy0uMTctLjQ1LS4yNS0uOTYtLjI1LTEuNTN6bTYuOTEtNi40NWgxLjU4djYuMTdoLjA1bDIuNTQtMy4xNmgxLjc3bC0yLjM1IDIuOCAyLjU5IDQuMDdoLTEuNzVsLTEuNzctMi45OC0xLjA4IDEuMjN2MS43NWgtMS41OHptMTMuNjkgMS4yN2MtLjI1LS4xMS0uNS0uMTctLjc1LS4xNy0uNTggMC0uODcuMzktLjg3IDEuMTZ2Ljc1aDEuMzR2MS4yN2gtMS4zNHY1LjZoLTEuNjF2LTUuNmgtLjkydi0xLjJsLjkyLS4wN3YtLjcyYzAtLjM1LjA0LS42OC4xMy0uOTguMDgtLjMxLjIxLS41Ny40LS43OXMuNDItLjM5LjcxLS41MWMuMjgtLjEyLjYzLS4xOCAxLjA0LS4xOC4yNCAwIC40OC4wMi42OS4wNy4yMi4wNS40MS4xLjU3LjE3em0uNDggNS4xOGMwLS41Ny4wOS0xLjA4LjI3LTEuNTMuMTctLjQ0LjQxLS44Mi43Mi0xLjEzLjMtLjMxLjY1LS41NCAxLjA0LS43MS4zOS0uMTYuOC0uMjQgMS4yMy0uMjRzLjg0LjA4IDEuMjQuMjRjLjQuMTcuNzQuNCAxLjA0Ljcxcy41NC42OS43MiAxLjEzYy4xOS40NS4yOC45Ni4yOCAxLjUzcy0uMDkgMS4wOC0uMjggMS41M2MtLjE4LjQ0LS40Mi44Mi0uNzIgMS4xM3MtLjY0LjU0LTEuMDQuNy0uODEuMjQtMS4yNC4yNC0uODQtLjA4LTEuMjMtLjI0LS43NC0uMzktMS4wNC0uN2MtLjMxLS4zMS0uNTUtLjY5LS43Mi0xLjEzLS4xOC0uNDUtLjI3LS45Ni0uMjctMS41M3ptMS42NSAwYzAgLjY5LjE0IDEuMjQuNDMgMS42Ni4yOC40MS42OC42MiAxLjE4LjYyLjUxIDAgLjktLjIxIDEuMTktLjYyLjI5LS40Mi40NC0uOTcuNDQtMS42NiAwLS43LS4xNS0xLjI2LS40NC0xLjY3LS4yOS0uNDItLjY4LS42My0xLjE5LS42My0uNSAwLS45LjIxLTEuMTguNjMtLjI5LjQxLS40My45Ny0uNDMgMS42N3ptNi40OC0zLjQ0aDEuMzNsLjEyIDEuMjFoLjA1Yy4yNC0uNDQuNTQtLjc5Ljg4LTEuMDIuMzUtLjI0LjctLjM2IDEuMDctLjM2LjMyIDAgLjU5LjA1Ljc4LjE0bC0uMjggMS40LS4zMy0uMDljLS4xMS0uMDEtLjIzLS4wMi0uMzgtLjAyLS4yNyAwLS41Ni4xLS44Ni4zMXMtLjU1LjU4LS43NyAxLjF2NC4yaC0xLjYxem0tNDcuODcgMTVoMS42MXY0LjFjMCAuNTcuMDguOTcuMjUgMS4yLjE3LjI0LjQ0LjM1LjgxLjM1LjMgMCAuNTctLjA3LjgtLjIyLjIyLS4xNS40Ny0uMzkuNzMtLjczdi00LjdoMS42MXY2Ljg3aC0xLjMybC0uMTItMS4wMWgtLjA0Yy0uMy4zNi0uNjMuNjQtLjk4Ljg2LS4zNS4yMS0uNzYuMzItMS4yNC4zMi0uNzMgMC0xLjI3LS4yNC0xLjYxLS43MS0uMzMtLjQ3LS41LTEuMTQtLjUtMi4wMnptOS40NiA3LjQzdjIuMTZoLTEuNjF2LTkuNTloMS4zM2wuMTIuNzJoLjA1Yy4yOS0uMjQuNjEtLjQ1Ljk3LS42My4zNS0uMTcuNzItLjI2IDEuMS0uMjYuNDMgMCAuODEuMDggMS4xNS4yNC4zMy4xNy42MS40Ljg0LjcxLjI0LjMxLjQxLjY4LjUzIDEuMTEuMTMuNDIuMTkuOTEuMTkgMS40NCAwIC41OS0uMDkgMS4xMS0uMjUgMS41Ny0uMTYuNDctLjM4Ljg1LS42NSAxLjE2LS4yNy4zMi0uNTguNTYtLjk0LjczLS4zNS4xNi0uNzIuMjUtMS4xLjI1LS4zIDAtLjYtLjA3LS45LS4ycy0uNTktLjMxLS44Ny0uNTZ6bTAtMi4zYy4yNi4yMi41LjM3LjczLjQ1LjI0LjA5LjQ2LjEzLjY2LjEzLjQ2IDAgLjg0LS4yIDEuMTUtLjYuMzEtLjM5LjQ2LS45OC40Ni0xLjc3IDAtLjY5LS4xMi0xLjIyLS4zNS0xLjYxLS4yMy0uMzgtLjYxLS41Ny0xLjEzLS41Ny0uNDkgMC0uOTkuMjYtMS41Mi43N3ptNS44Ny0xLjY5YzAtLjU2LjA4LTEuMDYuMjUtMS41MS4xNi0uNDUuMzctLjgzLjY1LTEuMTQuMjctLjMuNTgtLjU0LjkzLS43MXMuNzEtLjI1IDEuMDgtLjI1Yy4zOSAwIC43My4wNyAxIC4yLjI3LjE0LjU0LjMyLjgxLjU1bC0uMDYtMS4xdi0yLjQ5aDEuNjF2OS44OGgtMS4zM2wtLjExLS43NGgtLjA2Yy0uMjUuMjUtLjU0LjQ2LS44OC42NC0uMzMuMTgtLjY5LjI3LTEuMDYuMjctLjg3IDAtMS41Ni0uMzItMi4wNy0uOTVzLS43Ni0xLjUxLS43Ni0yLjY1em0xLjY3LS4wMWMwIC43NC4xMyAxLjMxLjQgMS43LjI2LjM4LjY1LjU4IDEuMTUuNTguNTEgMCAuOTktLjI2IDEuNDQtLjc3di0zLjIxYy0uMjQtLjIxLS40OC0uMzYtLjctLjQ1LS4yMy0uMDgtLjQ2LS4xMi0uNy0uMTItLjQ1IDAtLjgyLjE5LTEuMTMuNTktLjMxLjM5LS40Ni45NS0uNDYgMS42OHptNi4zNSAxLjU5YzAtLjczLjMyLTEuMy45Ny0xLjcxLjY0LS40IDEuNjctLjY4IDMuMDgtLjg0IDAtLjE3LS4wMi0uMzQtLjA3LS41MS0uMDUtLjE2LS4xMi0uMy0uMjItLjQzcy0uMjItLjIyLS4zOC0uM2MtLjE1LS4wNi0uMzQtLjEtLjU4LS4xLS4zNCAwLS42OC4wNy0xIC4ycy0uNjMuMjktLjkzLjQ3bC0uNTktMS4wOGMuMzktLjI0LjgxLS40NSAxLjI4LS42My40Ny0uMTcuOTktLjI2IDEuNTQtLjI2Ljg2IDAgMS41MS4yNSAxLjkzLjc2cy42MyAxLjI1LjYzIDIuMjF2NC4wN2gtMS4zMmwtLjEyLS43NmgtLjA1Yy0uMy4yNy0uNjMuNDgtLjk4LjY2cy0uNzMuMjctMS4xNC4yN2MtLjYxIDAtMS4xLS4xOS0xLjQ4LS41Ni0uMzgtLjM2LS41Ny0uODUtLjU3LTEuNDZ6bTEuNTctLjEyYzAgLjMuMDkuNTMuMjcuNjcuMTkuMTQuNDIuMjEuNzEuMjEuMjggMCAuNTQtLjA3Ljc3LS4ycy40OC0uMzEuNzMtLjU2di0xLjU0Yy0uNDcuMDYtLjg2LjEzLTEuMTguMjMtLjMxLjA5LS41Ny4xOS0uNzYuMzFzLS4zMy4yNS0uNDEuNGMtLjA5LjE1LS4xMy4zMS0uMTMuNDh6bTYuMjktMy42M2gtLjk4di0xLjJsMS4wNi0uMDcuMi0xLjg4aDEuMzR2MS44OGgxLjc1djEuMjdoLTEuNzV2My4yOGMwIC44LjMyIDEuMi45NyAxLjIuMTIgMCAuMjQtLjAxLjM3LS4wNC4xMi0uMDMuMjQtLjA3LjM0LS4xMWwuMjggMS4xOWMtLjE5LjA2LS40LjEyLS42NC4xNy0uMjMuMDUtLjQ5LjA4LS43Ni4wOC0uNCAwLS43NC0uMDYtMS4wMi0uMTgtLjI3LS4xMy0uNDktLjMtLjY3LS41Mi0uMTctLjIxLS4zLS40OC0uMzctLjc4LS4wOC0uMy0uMTItLjY0LS4xMi0xLjAxem00LjM2IDIuMTdjMC0uNTYuMDktMS4wNi4yNy0xLjUxcy40MS0uODMuNzEtMS4xNGMuMjktLjMuNjMtLjU0IDEuMDEtLjcxLjM5LS4xNy43OC0uMjUgMS4xOC0uMjUuNDcgMCAuODguMDggMS4yMy4yNC4zNi4xNi42NS4zOC44OS42N3MuNDIuNjMuNTQgMS4wM2MuMTIuNDEuMTguODQuMTggMS4zMiAwIC4zMi0uMDIuNTctLjA3Ljc2aC00LjM3Yy4wOC42Mi4yOSAxLjEuNjUgMS40NC4zNi4zMy44Mi41IDEuMzguNS4zIDAgLjU4LS4wNC44NC0uMTMuMjUtLjA5LjUxLS4yMS43Ni0uMzdsLjU0IDEuMDFjLS4zMi4yMS0uNjkuMzktMS4wOS41M3MtLjgyLjIxLTEuMjYuMjFjLS40NyAwLS45Mi0uMDgtMS4zMy0uMjUtLjQxLS4xNi0uNzctLjQtMS4wOC0uNy0uMy0uMzEtLjU0LS42OS0uNzItMS4xMy0uMTctLjQ0LS4yNi0uOTUtLjI2LTEuNTJ6bTQuNjEtLjYyYzAtLjU1LS4xMS0uOTgtLjM0LTEuMjgtLjIzLS4zMS0uNTgtLjQ3LTEuMDYtLjQ3LS40MSAwLS43Ny4xNS0xLjA4LjQ1LS4zMS4yOS0uNS43My0uNTcgMS4zem0zLjAxIDIuMjNjLjMxLjI0LjYxLjQzLjkyLjU3LjMuMTMuNjMuMi45OC4yLjM4IDAgLjY1LS4wOC44My0uMjNzLjI3LS4zNS4yNy0uNmMwLS4xNC0uMDUtLjI2LS4xMy0uMzctLjA4LS4xLS4yLS4yLS4zNC0uMjgtLjE0LS4wOS0uMjktLjE2LS40Ny0uMjNsLS41My0uMjJjLS4yMy0uMDktLjQ2LS4xOC0uNjktLjMtLjIzLS4xMS0uNDQtLjI0LS42Mi0uNHMtLjMzLS4zNS0uNDUtLjU1Yy0uMTItLjIxLS4xOC0uNDYtLjE4LS43NSAwLS42MS4yMy0xLjEuNjgtMS40OS40NC0uMzggMS4wNi0uNTcgMS44My0uNTcuNDggMCAuOTEuMDggMS4yOS4yNXMuNzEuMzYuOTkuNTdsLS43NC45OGMtLjI0LS4xNy0uNDktLjMyLS43My0uNDItLjI1LS4xMS0uNTEtLjE2LS43OC0uMTYtLjM1IDAtLjYuMDctLjc2LjIxLS4xNy4xNS0uMjUuMzMtLjI1LjU0IDAgLjE0LjA0LjI2LjEyLjM2cy4xOC4xOC4zMS4yNmMuMTQuMDcuMjkuMTQuNDYuMjFsLjU0LjE5Yy4yMy4wOS40Ny4xOC43LjI5cy40NC4yNC42NC40Yy4xOS4xNi4zNC4zNS40Ni41OC4xMS4yMy4xNy41LjE3LjgyIDAgLjMtLjA2LjU4LS4xNy44My0uMTIuMjYtLjI5LjQ4LS41MS42OC0uMjMuMTktLjUxLjM0LS44NC40NS0uMzQuMTEtLjcyLjE3LTEuMTUuMTctLjQ4IDAtLjk1LS4wOS0xLjQxLS4yNy0uNDYtLjE5LS44Ni0uNDEtMS4yLS42OHoiIGZpbGw9IiM1MzUzNTMiLz48L2c+PC9zdmc+)](https://crossmark.crossref.org/dialog/?doi=10.1038/s41746-025-01607-0)

### Cite this article

Zhou, S., Song, G., Sun, H. *et al.* Continuous sleep depth index annotation with deep learning yields novel digital biomarkers for sleep health. *npj Digit. Med.* **8**, 203 (2025). https://doi.org/10.1038/s41746-025-01607-0

[Download citation](https://citation-needed.springer.com/v2/references/10.1038/s41746-025-01607-0?format=refman&flavour=citation)

-   Received: 02 August 2024
    
-   Accepted: 30 March 2025
    
-   Published: 11 April 2025
    
-   Version of record: 11 April 2025
    
-   DOI: https://doi.org/10.1038/s41746-025-01607-0
    

### Share this article

Anyone you share the following link with will be able to read this content:

Get shareable link

Sorry, a shareable link is not currently available for this article.

Copy shareable link to clipboard

Provided by the Springer Nature SharedIt content-sharing initiative

[Download PDF](/articles/s41746-025-01607-0.pdf)

Advertisement

[![Advertisement](//pubads.g.doubleclick.net/gampad/ad?iu=/285/npjdigitalmed.nature.com/article&sz=300x250&c=-280699244&t=pos%3Dright%26type%3Darticle%26artid%3Ds41746-025-01607-0%26doi%3D10.1038/s41746-025-01607-0%26subjmeta%3D1816,375,617,692,700,784%26kwrd%3DQuality+of+life,Sleep+disorders)](//pubads.g.doubleclick.net/gampad/jump?iu=/285/npjdigitalmed.nature.com/article&sz=300x250&c=-280699244&t=pos%3Dright%26type%3Darticle%26artid%3Ds41746-025-01607-0%26doi%3D10.1038/s41746-025-01607-0%26subjmeta%3D1816,375,617,692,700,784%26kwrd%3DQuality+of+life,Sleep+disorders)

## Explore content

-   [Research articles](/npjdigitalmed/research-articles)
-   [Reviews & Analysis](/npjdigitalmed/reviews-and-analysis)
-   [News & Comment](/npjdigitalmed/news-and-comment)
-   [Collections](/npjdigitalmed/collections)

-   [Follow us on X](https://twitter.com/npjDigitalMed)
-   [Sign up for alerts](https://journal-alerts.springernature.com/subscribe?journal_id=41746)
-   [RSS feed](https://www.nature.com/npjdigitalmed.rss)

## About the journal

-   [Aims and scope](/npjdigitalmed/aims)
-   [Content types](/npjdigitalmed/content-types)
-   [Journal Information](/npjdigitalmed/journal-information)
-   [About the Editors](/npjdigitalmed/editors)
-   [Contact](/npjdigitalmed/contact)
-   [Journal Metrics](/npjdigitalmed/journal-impact)
-   [Calls for Papers](/npjdigitalmed/calls-for-papers)
-   [Editorial Policies](/npjdigitalmed/editorial-policies)
-   [About the Partner](/npjdigitalmed/partner)
-   [Open Access](/npjdigitalmed/open-access)
-   [Early Career Researcher Editorial Fellowship](/npjdigitalmed/editorial-fellowship)
-   [Editorial Team Vacancies](/npjdigitalmed/vacancies)
-   [News and Views Student Editor](/npjdigitalmed/news-and-views-student-editor)
-   [Communication Fellowship](/npjdigitalmed/communication-fellowship)

## Publish with us

-   [For Authors and Referees](/npjdigitalmed/for-authors-and-referees)
-   [Language editing services](https://authorservices.springernature.com/go/sn/?utm_source=For+Authors&utm_medium=Website_Nature&utm_campaign=Platform+Experimentation+2022&utm_id=PE2022)
-   [Open access funding](/npjdigitalmed/open-access-funding)
-   [Submit manuscript](https://submission.springernature.com/new-submission/41746/3)

## Search

Search articles by subject, keyword or author

Show results from All journals This journal

Search

[Advanced search](/search/advanced)

### Quick links

-   [Explore articles by subject](/subjects)
-   [Find a job](/naturecareers)
-   [Guide to authors](/authors/index.html)
-   [Editorial policies](/authors/editorial_policies/)

npj Digital Medicine (*npj Digit. Med.*)

ISSN 2398-6352 (online)

## nature.com footer links

### About Nature Portfolio

-   [About us](https://www.nature.com/npg_/company_info/index.html)
-   [Press releases](https://www.nature.com/npg_/press_room/press_releases.html)
-   [Press office](https://press.nature.com/)
-   [Contact us](https://support.nature.com/support/home)

### Discover content

-   [Journals A-Z](https://www.nature.com/siteindex)
-   [Articles by subject](https://www.nature.com/subjects)
-   [protocols.io](https://www.protocols.io/)
-   [Nature Index](https://www.natureindex.com/)

### Publishing policies

-   [Nature portfolio policies](https://www.nature.com/authors/editorial_policies)
-   [Open access](https://www.nature.com/nature-portfolio/for-authors/openaccess)

### Author & Researcher services

-   [Reprints & permissions](https://www.nature.com/reprints)
-   [Research data](https://www.springernature.com/gp/authors/research-data)
-   [Language editing](https://authorservices.springernature.com/language-editing/)
-   [Scientific editing](https://authorservices.springernature.com/scientific-editing/)
-   [Nature Masterclasses](https://masterclasses.nature.com/)
-   [Research Solutions](https://solutions.springernature.com/)

### Libraries & institutions

-   [Librarian service & tools](https://www.springernature.com/gp/librarians/tools-services)
-   [Librarian portal](https://www.springernature.com/gp/librarians/manage-your-account/librarianportal)
-   [Open research](https://www.nature.com/openresearch/about-open-access/information-for-institutions)
-   [Recommend to library](https://www.springernature.com/gp/librarians/recommend-to-your-library)

### Advertising & partnerships

-   [Advertising](https://partnerships.nature.com/product/digital-advertising/)
-   [Partnerships & Services](https://partnerships.nature.com/)
-   [Media kits](https://partnerships.nature.com/media-kits/)
-   [Branded content](https://partnerships.nature.com/product/branded-content-native-advertising/)

### Professional development

-   [Nature Awards](https://www.nature.com/immersive/natureawards/index.html)
-   [Nature Careers](https://www.nature.com/naturecareers/)
-   [Nature Conferences](https://conferences.nature.com)

### Regional websites

-   [Nature Africa](https://www.nature.com/natafrica)
-   [Nature China](http://www.naturechina.com)
-   [Nature India](https://www.nature.com/nindia)
-   [Nature Japan](https://www.natureasia.com/ja-jp)
-   [Nature Middle East](https://www.nature.com/nmiddleeast)

-   [Privacy Policy](https://www.nature.com/info/privacy)
-   [Use of cookies](https://www.nature.com/info/cookies)
-   Your privacy choices/Manage cookies
-   [Legal notice](https://www.nature.com/info/legal-notice)
-   [Accessibility statement](https://www.nature.com/info/accessibility-statement)
-   [Terms & Conditions](https://www.nature.com/info/terms-and-conditions)
-   [Your US state privacy rights](https://www.springernature.com/ccpa)
-   [Cancel contracts here](https://support.nature.com/de/support/solutions/articles/6000255911-kündigungsformular)

[![Springer Nature](/oscar-static/images/logos/sn-logo-white-c8f7a9c061.svg)](https://www.springernature.com/)

© 2026 Springer Nature Limited

Close banner Close

![Nature Briefing](/static/images/logos/nature-briefing-logo-n150-white-afc2e6ccc7.svg)

Sign up for the *Nature Briefing* newsletter — what matters in science, free to your inbox daily.

      Email address

  Sign up

 I agree my information will be processed in accordance with the *Nature* and Springer Nature Limited [Privacy Policy](https://www.nature.com/info/privacy).

Close banner Close

Get the most important science stories of the day, free in your inbox. [Sign up for Nature Briefing](https://www.nature.com/briefing/signup/?brieferEntryPoint=MainBriefingBanner)