% David R. Thompson
% Autumn 2012

% get bands from first endmember
jarosite = importdata('data/jarosite.dat',' ',16); 
use_bands = 10:5:450;
wl = jarosite.data(use_bands,1);
jarosite = jarosite.data(use_bands,2);

% load in two other endmembers, and a target signal
kaolinite = importdata('data/kaolinite.dat',' ',16);
kaolinite = interp1(kaolinite.data(:,1), kaolinite.data(:,2), wl);
muscovite = importdata('data/muscovite.dat',' ',16);
muscovite = interp1(muscovite.data(:,1), muscovite.data(:,2), wl);
olivine = importdata('data/olivine.dat',' ',16);
olivine = interp1(olivine.data(:,1), olivine.data(:,2), wl);

% compile our wrappers
mex dmsmf_mex.c libdms.a

% compute random mixing fractions
n = 128^2;
beta = [1+randn(n,1), 1+randn(n,1) 1+randn(n,1)];

% enforce positivity, and sum-to-one
beta(beta<0)=0.01;
beta = beta./repmat(sum(beta,2),[1 3]);

% construct the data matrix from random mixtures.  
D = beta(:,1) * jarosite' + beta(:,2)* kaolinite' + beta(:,3)*muscovite';
    
% plot results
close all;

mfracs=[0.05,0.1,0.15,0.2];

for m=1:numel(mfracs)
    
    mfrac = mfracs(m);

    % inject a single target at 10% mixing fraction, add random white noise
    target_idx = 5000;
    X = D; % local copy
    X(target_idx,:) = X(target_idx,:)*(1.0-mfrac) + olivine' * mfrac;
    X = X + randn(size(X,1),size(X,2)).*0.01;

    % plot representative spectra
    subplot(2,numel(mfracs),m);
    plot(wl, X(target_idx:(target_idx+50),:),'k');
    hold on; grid on; 
    xlabel('wavelength (microns)'); 
    if (m==1) ylabel('reflectance'); end
    plot(wl, X(target_idx,:),'r','Linewidth',2);
    title(sprintf('%2.0f%% fractional fill',mfrac*100));
    xlim([min(wl) max(wl)]);
    
    % test matched filter detection with FAM (as in DiPietro et al 2010)
    L = [olivine]';
    [mfv, md] = dmsmf_mex(single(X),single(L));

    % plot the results 
    subplot(2,numel(mfracs),numel(mfracs)+m);
    scatter(mfv,md,1,'k.');
    hold on; grid on; 
    xlabel('Matched filter score'); 
    if (m==1) ylabel('Mahalanobis distance'); end
    plot(mfv(target_idx), md(target_idx),'rx','linewidth',2);
    title('Target detection');
end
