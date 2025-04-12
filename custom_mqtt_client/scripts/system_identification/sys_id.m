clc
clear
close all


%% Get data

% Read the data from the text file (replace 'your_data.txt' with your file path)
data = load('sys_id_data.txt');  % Assuming your file is space-separated

% Extract timestamps, turnrate, and position from the loaded data
timestamps = data(:, 1)';  % First column is timestamps
turnrate = data(:, 2)';    % Second column is turnrate
position = data(:, 3)';    % Third column is position

% Find the index where turnrate transitions from 1 to 0
transition_idx = find(turnrate(1:end-1) == 1 & turnrate(2:end) == 0);

if ~isempty(transition_idx)
    % Filter the data before the transition point
    cutoff_idx = transition_idx(1);  % Get the first transition index
    timestamps = timestamps(1:cutoff_idx);  % Keep data up to the transition
    turnrate = turnrate(1:cutoff_idx);    % Keep data up to the transition
    position = position(1:cutoff_idx);    % Keep data up to the transition
end

% Normalize the time (optional, based on your preference)
time = timestamps - timestamps(1);  % Normalize time to start from zero

% Create an iddata object for system identification
sampling_time = mean(diff(timestamps));  % Calculate the average sampling time
id_data = iddata(position', turnrate', sampling_time);  % Create the iddata object


%% Plot
figure;
subplot(2,1,1);
plot(time, turnrate);
title('Input: Turnrate');
xlabel('Time (seconds)');
ylabel('Turnrate');
ylim([-0.1 1.1]);

subplot(2,1,2);
plot(time, position);
title('Output: Position');
xlabel('Time (seconds)');
ylabel('Position');


%% Estimate a Transfer Function
close all
sys = tfest(id_data, 3, 2);

% Display the estimated transfer function
disp('Estimated Transfer Function:');
disp(sys);

% Compare the model output to the actual data
figure;
compare(id_data, sys);


%% Tune controller

Kp = 3.0;  % Example LINE_KP
tauZ = 10;  % Example tauZ
tauP = 0.1;  % Example tauP

% Define the P-lead controller transfer function
s = tf('s');
C = Kp * (1 + tauZ * s) / (1 + tauP * s);

% Open the PID Tuner with your system and controller
pidTuner(sys, C);

% Create the closed-loop transfer function
closedLoopSys = feedback(C * sys, 1);

% Simulate the step response to see the system's behavior
t = 0:0.01:10;  % Time vector
figure;
step(closedLoopSys, t);
title('Closed-Loop Step Response with P-Lead Controller');

% Bode plot to analyze frequency response
figure;
bode(closedLoopSys);



















