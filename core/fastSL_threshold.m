function fastSL_threshold(model, threshold, cutoff, order, eliList, atpm)
%% fastSL(model,cutoff,order,eliList,atpm)
% Requires the openCOBRA toolbox
% http://opencobra.sourceforge.net/openCOBRA/Welcome.html
% 
% INPUT
% model (the following fields are required - others can be supplied)       
%   S            Stoichiometric matrix
%   b            Right hand side = dx/dt
%   c            Objective coefficients
%   lb           Lower bounds
%   ub           Upper bounds
%   rxns         Reaction Names
%OPTIONAL
% threshold      threshold flux for active/non-zero reaction. Default is 0.
% cutoff         cutoff percentage value for lethality.Default is 0.01.
% order          Order of SLs required.Default order is 2. Max value 3.
% eliList        List of reactions to be ignored for lethality
%                analysis:Exchange Reactions, ATPM etc.
% atpm           ATPM Reaction Id in model.rxns if other than 'ATPM'
% 
%
% Aditya Pratapa        06/26/14. 
% N Sowmya Manojna      06/03/21.

    %%
    %initCobraToolbox
    if exist('threshold', 'var')
        if isempty(threshold)
            threshold = 0;
        end
    else
        threshold = 0;
    end

    if exist('cutoff', 'var')
        if isempty(cutoff)
            cutoff = 0.01;
        end
    else
        cutoff = 0.01;
    end

    if exist('order', 'var')
        if isempty(order)
            order = 2;
        else
            if (order>3)
            err = MException('ResultChk:OutOfRange', ...
            'Resulting value is outside expected range. Maximum value is 3.');
             throw(err)
            end
        end
    else
        order = 2;
    end


    %Please change this according to your model
    if exist('atpm', 'var')
        if isempty(atpm)
            atpm = 'ATPM'; %Reaction Id of ATP maintenance reaction- by default it takes 'ATPM'
        end
    else
        atpm = 'ATPM';
    end


    if exist('eliList', 'var')
        if isempty(eliList)
            eliList = model.rxns(ismember(model.rxns, atpm)); %To eliminate ATPM.
        end
    else
        eliList = model.rxns(ismember(model.rxns,atpm));
    end

    fname = strcat(model.description,'_Rxn_lethals.mat');

    switch order
        case 1
            [Jsl] = singleSL_threshold(model, threshold, cutoff, eliList, atpm);
           
            fprintf('\nSaving Single Lethal Reactions List... ');
            save(fname,'Jsl');
            fprintf('Done. \n');
        case 2
            [Jsl,Jdl] = doubleSL_threshold(model, threshold, cutoff, eliList, atpm);
         
            fprintf('\nSaving Single and Double Lethal Reactions List... ');
            save(fname,'Jsl');
            save(fname,'Jdl','-append');
            fprintf('Done. \n');
        case 3
            [Jsl,Jdl,Jtl]=tripleSL_threshold(model, threshold, cutoff, eliList, atpm);
          
            fprintf('\nSaving Single, Double and Triple Lethal Reactions List... ');
            save(fname,'Jsl');
            save(fname,'Jdl','-append');
            save(fname,'Jtl','-append');
            fprintf('Done. \n');
    end
end

function [Jsl] = singleSL_threshold(model, threshold, cutoff, eliList, atpm)
%% [Jsl] = singleSL(model,cutoff,eliList,atpm)
% INPUT
% model (the following fields are required - others can be supplied)       
%   S            Stoichiometric matrix
%   b            Right hand side = dx/dt
%   c            Objective coefficients
%   lb           Lower bounds
%   ub           Upper bounds
%   rxns         Reaction Names
% OPTIONAL
% threshold      threshold flux for active/non-zero reaction. Default is 0.
% cutoff         cutoff percentage value for lethality.Default is 0.01.
% eliList        List of reactions to be ignored for lethality
%                analysis: Exchange Reactions, ATPM etc.
% atpm           ATPM Reaction Id in model.rxns if other than 'ATPM'
% OUTPUT
% Jsl            Single lethal reactions identified
% 
% Aditya Pratapa        6/26/14. 
% N Sowmya Manojna      3 July, 2021

    if exist('threshold', 'var')
        if isempty(threshold)
            threshold = 0;
        end
    else
        threshold = 0;
    end

    if exist('cutoff', 'var')
        if isempty(cutoff)
            cutoff = 0.01;
        end
    else
        cutoff = 0.01;
    end

    if exist('atpm', 'var')
        if isempty(atpm)
            atpm = 'ATPM'; %Reaction Id of ATP maintenance reaction- by default it takes 'ATPM'
        end
    else
        atpm = 'ATPM';
    end

    if exist('eliList', 'var')
        if isempty(eliList)
            eliList = model.rxns(ismember(model.rxns, atpm)); % To eliminate ATPM.
        end
    else
        eliList = model.rxns(ismember(model.rxns, atpm));
    end

    Jsl = [];

    % Step 1 Identify Single Lethal Reactions...
    % Identify minNorm flux distribution
    solWT = optimizeCbModel(model, 'max', 'one');
    grWT = solWT.f;

    % Consider greater than threshold than ~= 0
    Jnz = find(abs(solWT.x) > threshold);

    if (~isempty(eliList))
        % Index of reactions not considered for lethality analysis
        eliIdx = find(ismember(model.rxns, eliList));
        % Jnz
        Jnz = Jnz(~ismember(Jnz, eliIdx));
    end
    h = waitbar(0,'0.00','Name','Identifying Jsl...');

    % Identify Single Lethal Reaction Deletions...
    modeldel = model;

    for iRxn = 1:length(Jnz)
        delIdx_i = Jnz(iRxn);
        modeldel.lb(delIdx_i) = 0;
        modeldel.ub(delIdx_i) = 0;

        solKO_i = optimizeCbModel(modeldel);
        if (solKO_i.f<cutoff*grWT || isnan(solKO_i.f))
            Jsl = [Jsl;delIdx_i];
        end
       % Reset bounds on idx reaction
        modeldel.lb(delIdx_i) = model.lb(delIdx_i);
        modeldel.ub(delIdx_i) = model.ub(delIdx_i);
        waitbar(iRxn/length(Jnz),h,[num2str(round(iRxn*100/length(Jnz))) '% completed...']);

    end
    close(h);
    Jsl = model.rxns(Jsl);
end

function [Jsl,Jdl] = doubleSL_threshold(model, threshold, cutoff, eliList, atpm)
%% [Jsl,Jdl] = doubleSL_threshold(model,cutoff,eliList,atpm)
% INPUT
% model (the following fields are required - others can be supplied)       
%   S            Stoichiometric matrix
%   b            Right hand side = dx/dt
%   c            Objective coefficients
%   lb           Lower bounds
%   ub           Upper bounds
%   rxns         Reaction Names
% OPTIONAL
% threshold      threshold flux for active/non-zero reaction. Default is 0.
% cutoff         cutoff percentage value for lethality.Default is 0.01.
% eliList        List of reactions to be ignored for lethality
%                analysis:Exchange Reactions, ATPM etc.
% atpm           ATPM Reaction Id in model.rxns if other than 'ATPM'
% OUTPUT
% Jsl            Indices of single lethal reactions identified
% Jdl            Indices of double lethal reactions identified
%
% Aditya Pratapa       6/26/14. 
% N Sowmya Manojna      3 July, 2021

    if exist('threshold', 'var')
        if isempty(threshold)
            threshold = 0;
        end
    else
        threshold = 0;
    end

    if exist('cutoff', 'var')
        if isempty(cutoff)
            cutoff = 0.01;
        end
    else
        cutoff = 0.01;
    end

    if exist('eliList', 'var')
        if isempty(eliList)
            eliList = model.rxns(ismember(model.rxns,'ATPM')); %To eliminate ATPM.
        end
    else
        eliList = model.rxns(ismember(model.rxns,'ATPM'));
    end

    solWT = optimizeCbModel(model, 'max', 'one');
    grWT = solWT.f;
    Jnz = find(abs(solWT.x) > threshold);

    if (~isempty(eliList))
        eliIdx = find(ismember(model.rxns,eliList));
        Jnz = Jnz(~ismember(Jnz,eliIdx)); %Jnz
    end

    Jsl = singleSL_threshold(model, threshold, cutoff, eliList);
    Jsl = find(ismember(model.rxns, Jsl));
    Jnz_copy = Jnz(~ismember(Jnz, Jsl)); %Jnz-Jsl

    Jdl = [];

    %%
    h = waitbar(0,'0.00','Name','Identifying Jdl - Part 1 of 2...');

    modeldel = model;
    for iRxn = 1:length(Jnz_copy)
        
        delIdx_i = Jnz_copy(iRxn);
        modeldel.lb(delIdx_i) = 0;
        modeldel.ub(delIdx_i) = 0;

        solKO_i = optimizeCbModel(modeldel,'max','one');
        % Consider greater than threshold than  neq 0
        newnnz = find(abs(solKO_i.x) > threshold);
        Jnz_i = newnnz(~ismember(newnnz, Jnz));
        
        if (~isempty(eliList))
            Jnz_i = Jnz_i(~ismember(Jnz_i, eliIdx));
        end
        
        for jRxn = 1:length(Jnz_i)
            delIdx_j = Jnz_i(jRxn);
            modeldel.lb(delIdx_j) = 0;
            modeldel.ub(delIdx_j) = 0;
            
            solKO_ij = optimizeCbModel(modeldel);
            if (solKO_ij.f < cutoff*grWT || isnan(solKO_ij.f))
                Jdl = [Jdl;delIdx_i delIdx_j];
            end

            % Reset bounds on idx1 reaction
            modeldel.lb(delIdx_j) = model.lb(delIdx_j);
            modeldel.ub(delIdx_j) = model.ub(delIdx_j);
        end

        % Reset bounds on idx reaction
        modeldel.lb(delIdx_i) = model.lb(delIdx_i);
        modeldel.ub(delIdx_i) = model.ub(delIdx_i);
        waitbar(iRxn/length(Jnz_copy),h,[num2str(round(iRxn*100/length(Jnz_copy))) '% completed...']);

    end
    close(h);

    %%
    h = waitbar(0,'0.00','Name','Identifying Jdl - Part 2 of 2...');

    for iRxn = 1:length(Jnz_copy)
        for jRxn = 1:length(Jnz_copy)
            if (jRxn<iRxn)
                modeldel = model;
                delIdx_i = Jnz_copy(iRxn);
                delIdx_j = Jnz_copy(jRxn);
                
                modeldel.lb(delIdx_i) = 0;
                modeldel.ub(delIdx_i) = 0;
                
                modeldel.lb(delIdx_j) = 0;
                modeldel.ub(delIdx_j) = 0;
                
                solKO_ij = optimizeCbModel(modeldel);
                if (solKO_ij.f<cutoff*grWT || isnan(solKO_ij.f))
                    Jdl = [Jdl;delIdx_i delIdx_j];
                end
            else
                break;
            end
        end

        waitbar(iRxn*(iRxn-1)/(length(Jnz_copy)*(length(Jnz_copy)-1)),h,[num2str(round(iRxn*(iRxn-1)*100/(length(Jnz_copy)*(length(Jnz_copy)-1)))) '% completed...']);
    end

    close(h);
    Jsl = model.rxns(Jsl);
    Jdl = model.rxns(Jdl);

    fprintf('\n Done...');
end
