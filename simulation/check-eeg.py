# %%
import mne

# %%
raw = mne.io.read_raw_fif('test-1hr-32-raw.fif')
events, event_id = mne.events_from_annotations(raw)
print(raw)
print(events, event_id)

# %%
epochs = mne.Epochs(raw, events, event_id)
print(epochs)

# %%
for _, evt in epochs.event_id.items():
    evoked = epochs[evt].average()
    print(evt)
    evoked.plot_joint()

# %%
mne.viz.plot_events(events, sfreq=1000, event_id=event_id)
print()

# %%
data = epochs.get_data()
# %%
mne.viz.plot_sensors(epochs.info, show_names=True)
print(', '.join(epochs.info['ch_names']))
# %%
