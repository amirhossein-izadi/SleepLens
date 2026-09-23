# 09 Leakage + splits

## Risks
- Critical: 2 nights/subject — never split nights across train/val/test.
- High: global z-score / full-data preprocessing / epoch shuffle.
- Medium: tech-ID in filename, lights-off/SOL as feature, ?/Mov train-test mismatch, SC/ST EMG joint norm.
- Low: duplicates (none; 0 missing pairs).
## Proposal (subject-wise 70/15/15, stratified SC/ST, nights paired)
Train 69 subj / 135 rec / 331264 ep (wake199653 n117778 n259840 n313905 rem23241); Val 15/30/74832; Test 16/32/77323. Lists: tables/split_proposal.txt. Alt: grouped 5-fold.
