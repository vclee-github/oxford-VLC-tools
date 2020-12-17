%% Vincent Lee
%% vincent.lee@eng.ox.ac.uk

%THIS CODE IS FOR R2018b. SOME FUNCTIONS WILL NOT WORK IN NEWER MATLAB
%VERSIONS.

%This R2018b code will capture the spectrum trace on the Agilent 86142B OSA
%and save the trace x and y values (wavelength and power) to text files in csv format. 
%There will be 2 files: wide spectrum and then narrow spectrum, and each span can be 
%configured. The code will also plot the same traces in Matlab.

%Start by running GPIB Configurator for the Prologix Controller by itself.
%Set up the parameters for the Prologix device as Controller and the GPIB
%Address.
%Plug in GPIB Prologix device into instrument (e.g OSA) and query *IDN? to
%ensure connectivity.
%Click exit and then open up Matlab and run Instrument Control.
%Click on the COM port (e.g. COM11 in this instance) and click Connect.
%Now you may run this program.

%%
clear all;
clc;

%% Connect Agilent 86142B OSA using COM

% Find a serial port object. (note: serialport function is used in R2019a)
osa = instrfind('Type', 'serial', 'Port', 'COM11', 'Tag', '');

% Set osa serial parameters
osa.BaudRate = 9600;
osa.DataBits = 8;
osa.Parity = 'None';
osa.InputBufferSize = 65536;
osa.Terminator = 'LF';
set(osa, 'Timeout', 10);

% Create the serial port object if it does not exist
% otherwise use the object that was found.
if isempty(osa)
    osa = serial('COM11');
else
    fclose(osa);
    osa = osa(1);
end

% Connect to instrument object, osa.
fopen(osa);

% Communicating with instrument object, osa.
data = query(osa, '*IDN?');

%% Initialization

% Autoscale/Automeasure
fprintf(osa, sprintf('DISP:WIND:TRAC:ALL:SCAL:AUTO; *OPC?')); %Auto sets to dBm.

% Set up the OSA
fprintf(osa, sprintf('DISP:TRAC:Y:RLEV 0 dbm'));  %Set the display dB reference level - the maximum power expected to display. 
%There is no reference level LINE for Linear scale. It is only at the top of the
%screen. So RLEV command does not work. Need to use SRL instead.

fprintf(osa, sprintf('DISP:WIND:TRAC:Y:SPAC LIN')); %Set to Linear scale
%fprintf(osa, sprintf('DISP:TRAC:Y:LIN ON')); %Same as above

%% Prompt user to start the next set of parameters after wavelength settings
%This pause is necessary otherwise a Timeout occurs. Instrument can't read 
%the following commands while still adjusting screen parameters.
prompt = 'Press Enter After Screen Settles';
keypress = input(prompt);

%% First set of parameters for wide spectrum view
% Set up OSA window centering around 1370 nm
fprintf(osa, sprintf('SENS:WAV:STAR 1369 NM'));  %Set start wavelength on screen
fprintf(osa, sprintf('SENS:WAV:STOP 1372 NM'));  %Set stop wavelength on screen

% Marker 1 to peak on Trace A
fprintf(osa, sprintf('CALC1:MARK1:STAT ON'));  %Turn Marker 1 On.
fprintf(osa, sprintf('CALC1:MARK1:MAX'));  %Set marker 1 to peak (the maximum amplitude point)

% Take initial sweep
fprintf(osa, sprintf('INIT:IMM; *OPC?'));  %Take a sweep. Freezes frame.

%% Trace Wide Spectrum

%Sweep is different than Trace. Sweep is an active view on the OSA. Trace is a waveform that can be saved.

%INIT:IMM is initialize immediate sweep which will show you the data you want to see on screen. 
%Then you need to activate a Trace, feed it live data, and then freeze/hold that data into the Trace.

% For Troubleshooting: Query the x (wavelength) and y (power) values of this marker
mkrWl_1 = 0;
mkrWl_1 = str2double(query(osa, 'CALC1:MARK1:X?'));
mkrWl_1 = str2double(query(osa, 'CALC1:MARK1:X?'));  %Make second query to ensure data is retrieved

mkrAmp_1 = 0;
mkrAmp_1 = str2double(query(osa, 'CALC1:MARK1:Y?'));
mkrAmp_1 = str2double(query(osa, 'CALC1:MARK1:Y?'));

fprintf(osa, sprintf('SENS:SWE:POIN 1001')); %Set sweep to 1001 points

% Query settings
x_start_1 = str2double(query(osa, 'TRAC:DATA:X:STAR? TRA'));  %Start Wavelength
x_stop_1 = str2double(query(osa, 'TRAC:DATA:X:STOP? TRA'));  %Stop Wavelength

num_points = str2double(query(osa, 'SENS:SWE:POIN?'));  %Number of sweep data points

% Query only works for live data. Not a loaded spectrum. 
[y_data_1, count_1] = query(osa, 'TRAC:DATA:Y? TrA'); %ASCII csv format. 1 Cell with all values separated by commas.


%% Second set of parameters to narrow spectrum view

% Marker 1 to peak on Trace A
fprintf(osa, sprintf('CALC1:MARK1:STAT ON'));  %Turn Marker 1 On.
fprintf(osa, sprintf('CALC1:MARK1:MAX'));  %Set marker 1 to peak (the maximum amplitude point)
fprintf(osa, sprintf('CALC1:MARK1:SCEN'));  %Set marker 1 to spectrum center
fprintf(osa, sprintf('SENS:WAV:SPAN 0.2 NM'));  %Set span on screen

% Take another sweep
fprintf(osa, sprintf('INIT:IMM; *OPC?'));  %Take a sweep. Freezes screen.

fprintf(osa, sprintf('CALC1:MARK1:MAX'));  %Set marker 1 to peak (the maximum amplitude point)
%fprintf(osa, sprintf('CALC1:MARK1:SRL'));  %Set marker 1 to reference level
fprintf(osa, sprintf('CALC1:MARK1:SCEN'));  %Set marker 1 to spectrum center

%Auto align to the marker does the same as spectrum center because you have
%marker 1 set to the peak
%fprintf(osa, sprintf('CAL:ALIG:MARK1;*OPC?'));

%% Trace Narrow Spectrum

% For Troubleshooting: Query the x (wavelength) and y (power) values of this marker
mkrWl_2 = 0;
mkrWl_2 = str2double(query(osa, 'CALC1:MARK1:X?'));
mkrWl_2 = str2double(query(osa, 'CALC1:MARK1:X?'));  %Make second query to ensure data is retrieved

mkrAmp_2 = 0;
mkrAmp_2 = str2double(query(osa, 'CALC1:MARK1:Y?'));
mkrAmp_2 = str2double(query(osa, 'CALC1:MARK1:Y?'));

fprintf(osa, sprintf('SENS:SWE:POIN 1001')); %Set sweep to 1001 points

% Query settings
x_start_2 = str2double(query(osa, 'TRAC:DATA:X:STAR? TRA'));  %Start Wavelength
x_stop_2 = str2double(query(osa, 'TRAC:DATA:X:STOP? TRA'));  %Stop Wavelength

% Query only works for live data. Not a loaded spectrum. 
[y_data_2, count_2] = query(osa, 'TRAC:DATA:Y? TrA'); %ASCII csv format. 1 Cell with all values separated by commas.

% Disconnect OSA
fclose(osa);

%% Plot and Save to Text File

wavelength_1=zeros(num_points,1);
step_1=(x_stop_1 - x_start_1)/(num_points-1);

wavelength_2=zeros(num_points,1);
step_2=(x_stop_2 - x_start_2)/(num_points-1);

for i=1:1:num_points
wavelength_1(i,1) = (x_start_1+(step_1*(i-1)));
wavelength_2(i,1) = (x_start_2+(step_2*(i-1)));
end

y_data_1_split = str2double(split(y_data_1,","));
y_data_2_split = str2double(split(y_data_2,","));

% figure
% plot(wavelength_1,y_data_1_split);
% xlabel('Wavelength')
% ylabel('Watts')

spectrum_wide = zeros(num_points,2);
spectrum_wide(:,1) = wavelength_1(:,1);
spectrum_wide(:,2) = y_data_1_split(:,1);

figure
plot(spectrum_wide(:,1),spectrum_wide(:,2))
xlabel('Wavelength')
ylabel('Watts')

% Save spectrum to text file (note: writematrix function is used in R2019a)
%dlmwrite('spectrum_wide.txt',spectrum_wide);
dlmwrite('spectrum_wide.txt',spectrum_wide,'precision','%.20f');

% figure
% plot(wavelength_2,y_data_2_split);
% xlabel('Wavelength')
% ylabel('Watts')

spectrum_narrow = zeros(num_points,2);
spectrum_narrow(:,1) = wavelength_2(:,1);
spectrum_narrow(:,2) = y_data_2_split(:,1);

figure
plot(spectrum_narrow(:,1),spectrum_narrow(:,2))
xlabel('Wavelength')
ylabel('Watts')

% Save spectrum to text file (note: writematrix function is used in R2019a)
%dlmwrite('spectrum_narrow.txt',spectrum_narrow);
dlmwrite('spectrum_narrow.txt',spectrum_narrow,'precision','%.20f');
