import mne

epochs = mne.read_epochs('./output/example/clean_epo.fif')
print(epochs)
