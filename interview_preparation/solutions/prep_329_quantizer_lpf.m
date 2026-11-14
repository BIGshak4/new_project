% Three-bit midrise quantizer on [0,1] V.
xgrid = ((0:8191) + 0.5)/8192;
code = min(7,floor(8*xgrid));
estimate = (code + 0.5)/8;
errorV = estimate - xgrid;
counts = accumarray(code(:) + 1, 1, [8,1]);
assert(all(counts == 1024));
assert(max(abs(errorV)) <= 1/16);

figure;
subplot(2,1,1);
bar(0:7,counts/numel(code));
xlabel('Code'); ylabel('Probability');
subplot(2,1,2);
plot(xgrid,errorV,'.','MarkerSize',2);
xlabel('Input (V)'); ylabel('Estimate - input (V)');

% Filter a separate sampled test signal. Default filter state is zero.
fs = 1000;
fc = 100;
t = (0:999)/fs;
x = 0.5 + 0.30*sin(2*pi*20*t) + 0.15*sin(2*pi*300*t);
g = tan(pi*fc/fs);
b = [g, g]/(1+g);
a = [1, (g-1)/(g+1)];
y = filter(b,a,x);
figure;
plot(t,x,t,y);
xlim([0 0.1]); xlabel('Time (s)'); ylabel('Voltage (V)');
legend('Input','Filtered');
z = exp(-1i*2*pi*fc/fs);
assert(abs(abs((b(1)+b(2)*z)/(1+a(2)*z)) - 1/sqrt(2)) < 1e-12);
