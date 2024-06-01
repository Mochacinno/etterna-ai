import librosa
import numpy as np
import tempoEstimator
import utils

def find_section_label(start_measure_time, musical_sections):
    for section_label, start_time, end_time in musical_sections:
        if start_time <= start_measure_time < end_time:
            return section_label
    return None

# TO review
def find_best_subdivision_level(measure_time, min_interval):
    #print(f"measure_time: {measure_time} with min_interval {min_interval}")
    # Consider common musical subdivisions: 1, 2, 4, 8, 16, 32, etc.
    common_subdivisions = [2**i for i in range(6)]  # Up to 32th note
    for subdivision in common_subdivisions:
        interval = measure_time / subdivision
        #print(abs(interval - min_interval))
        if abs(interval - min_interval) < 50:
            return subdivision
    return max(common_subdivisions)

def generate_chart(onset_times, bpms, song_duration, smooth_rms, rms_threshold, musical_sections):
    beatmap = []
    
    start_bpm = bpms[0][0]

    measure_time = calculate_measure_time(start_bpm)
    
    #print(f"measure_time: {measure_time}")
    
    start_time = onset_times[0]
    bpms = bpms
    start_measure_time = start_time
    index_onset = 0

    while start_measure_time <= song_duration:
        #print(f"start_measure_time: {start_measure_time}")
        #print(f"measure_time: {measure_time}")
        onsets_in_measure, index_onset = collect_onsets_in_measure(onset_times, start_measure_time, measure_time, index_onset)
        #print(f"raw: {onsets_in_measure}")
        #if len(onsets_in_measure) == 0:
        #    beats_per_measure = generate_empty_measure()
        #else:
        #    beats_per_measure, index_onset = generate_beats(onsets_in_measure, measure_time, start_measure_time, index_onset, smooth_rms, rms_threshold)
        beats_per_measure, index_onset = generate_beats(onsets_in_measure, measure_time, start_measure_time, index_onset, smooth_rms, rms_threshold, musical_sections)
        
        beatmap.append(beats_per_measure)
        start_measure_time += measure_time
        
        # Update measure time based on BPM changes
        bpm = utils.bpm_for_time(bpms, start_measure_time)
        #print(f"for bpm: {bpm}")
        measure_time = calculate_measure_time(bpm)
    return beatmap, start_time

def calculate_measure_time(bpm):
    # calculates ( 60 / bpm ) * 4
    return int(240000 / bpm)

def collect_onsets_in_measure(onset_times, start_measure_time, measure_time, index_onset):
    end_measure_time = start_measure_time + measure_time
    #print(f"end_measure_time: {end_measure_time}")
    onsets_in_measure = []

    #print("ONSET WINDOW")
    while index_onset < len(onset_times) and start_measure_time <= onset_times[index_onset] < end_measure_time:
        #print(onset_times[index_onset])
        onsets_in_measure.append(onset_times[index_onset])
        index_onset += 1
    
    return onsets_in_measure, index_onset

def generate_empty_measure():
    return [np.zeros(4, dtype=int) for _ in range(4)]

# Main function to generate beats
def generate_beats(onsets_in_measure, measure_time, start_measure_time, index_onset, smooth_rms, rms_threshold, musical_sections, sr=22050):
    # Find the section label for the current measure time
    current_section_label = find_section_label(start_measure_time, musical_sections)
    print(f"current_section_label: {current_section_label} for start_measure_time: {start_measure_time}")

    # Static variables to store section notes and track the active section
    if not hasattr(generate_beats, 'section_notes_dict'):
        generate_beats.section_notes_dict = {}
        generate_beats.active_section_label = None

    section_notes_dict = generate_beats.section_notes_dict

    # Ensure section dictionary structure
    if current_section_label is not None:
        if current_section_label not in section_notes_dict:
            section_notes_dict[current_section_label] = []
        section_measures = section_notes_dict[current_section_label]
        
        # Determine the measure index within the section
        current_measure_index = (start_measure_time - min(start for _, start, end in musical_sections if start <= start_measure_time < end)) // measure_time
        current_measure_index = int(current_measure_index)
        
        # Check if the current measure has already been generated
        if current_measure_index < len(section_measures):
            return section_measures[current_measure_index], index_onset
    else:
        generate_beats.active_section_label = None
        beats_per_measure = []

    #print(f"dict: {generate_beats.section_notes_dict}")

    # Convert start_measure_time to frames and check RMS
    frame_index = librosa.time_to_frames(start_measure_time / 1000, sr=sr)
    ideal_subdivision = 8 if smooth_rms[frame_index] > rms_threshold else 4

    # Quantize onsets
    #onsets_in_measure = quantize_onsets(onsets_in_measure, measure_time, ideal_subdivision, start_measure_time)

    # Generate beats for the measure
    beats_per_measure = []
    beat = start_measure_time
    for _ in range(ideal_subdivision):
        group = np.zeros(4, dtype=int)
        group[np.random.randint(0, 4)] = 1
        beats_per_measure.append(group)
        beat += measure_time / ideal_subdivision

     # Store the generated beats in the dictionary if they belong to a section
    if current_section_label is not None:
        section_notes_dict[current_section_label].append(beats_per_measure)
    
    return beats_per_measure, index_onset

def quantize_onsets(onsets, measure_time, subdivisions, start_measure_time, index_onset):
    
    interval = measure_time // subdivisions
    end_measure_time = start_measure_time + measure_time
    grid_points = np.arange(start_measure_time, end_measure_time + interval, interval)
    
    quantized_onsets = [min(grid_points, key=lambda x: abs(x - onset)) for onset in onsets]
    
    if end_measure_time == max(quantized_onsets):
        #print(f"{onset_times[index_onset - 1]} was replaced")
        onset_times[index_onset - 1] = max(quantized_onsets)
        index_onset -= 1
    return quantized_onsets, index_onset

def chartFileCreation(beatmap, bpms, start_time, song):
    # Format note start time
    text_content = "START_TIME:\n"
    text_content += str(start_time)+"\n"
    # Format BPMS into text content
    text_content += "BPMS:\n"
    for bpm, start_time in bpms:
        text_content += f"{start_time}:{bpm},\n"
    # Format beatmap notes into text content
    text_content += "NOTES:\n"
    for groups in beatmap:
        for group in groups:
            text_content += ''.join(map(str, group))  # Convert group to string and append to text content
            text_content += "\n"
        text_content += ",\n"  # Add comma and newline after every measure
    
    # Write text content to a file
    output_file = "Music+Beatmaps/"+song+".txt"
    with open(output_file, 'w') as file:
        file.write(text_content)
    
    print(f"Text file '{output_file}' generated successfully.")

# main code
song_name = "nhelv"
y, sr = librosa.load("Music+Beatmaps/"+song_name+".mp3")

#y = utils.slice_music(y, sr, 40, 100)

#y = utils.audioFilter(y, sr)

onset_times = utils.onset_detection(y, sr)
# utils.createClickTrack(y, sr, onset_times / 1000, song_name+"click")

#bpms = tempoEstimator.bpm_changes(tempoEstimator.tempoEstimate((y, sr)), onset_times[0])
#print(bpms)
bpms = [(utils.find_best_tempo(y, sr), 0)] # for the current version, we assume CONSTANT tempo
print(bpms)
song_duration = librosa.get_duration(y=y, sr=sr) * 1000

# TODO change to one function such as a generate_chart_init which prepares all the values
rms_values = librosa.feature.rms(y=y)[0]
smoothed_rms = utils.smooth_rms(rms_values)
rms_threshold = utils.find_rms_threshold(smoothed_rms, sr)
musical_sections = utils.segmentAnalysis(y, sr)
print(musical_sections)

beatmap, start_time = generate_chart(onset_times, bpms, song_duration, smoothed_rms, rms_threshold, musical_sections)

chartFileCreation(beatmap, bpms, start_time, song_name)