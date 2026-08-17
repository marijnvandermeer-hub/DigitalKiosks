"""Reproduce the core tables and figures reported for Digital Kiosks Activity 1.4.

Input: six harmonised city CSV files in data/harmonized/.
Output: report-ready tables and figures in outputs/.

This script intentionally excludes exploratory analyses and dashboard code that are not
used in the final report.
"""
from pathlib import Path
import warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy.stats import norm
from scipy.special import expit
from patsy import build_design_matrices

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "analysis_ready"
OUT = ROOT / "outputs"
TABLES = OUT / "tables"
FIGURES = OUT / "figures"
TABLES.mkdir(parents=True, exist_ok=True)
FIGURES.mkdir(parents=True, exist_ok=True)

CITY_FILES = {
    "Bergen": DATA / "Bergen_analysis_ready.csv",
    "Gothenburg": DATA / "Gothenburg_analysis_ready.csv",
    "Saint Quentin": DATA / "SaintQuentin_analysis_ready.csv",
    "Sint Niklaas": DATA / "SintNiklaas_analysis_ready.csv",
    "Antwerpen": DATA / "Antwerpen_analysis_ready.csv",
    "Hamburg": DATA / "Hamburg_analysis_ready.csv",
}
CITY_HOUSEHOLDS = {
    "Bergen": 140200, "Gothenburg": 267000, "Saint Quentin": 30609,
    "Sint Niklaas": 35047, "Antwerpen": 206660, "Hamburg": 235438,
}
ITEM_LABELS = {
    "vacuum_cleaner": "Vacuum cleaner", "steam_cleaner": "Steam cleaner",
    "drill": "Drill", "video_projector": "Video projector",
    "hand_sander": "Hand sander", "fitness_equipment": "Fitness equipment/devices",
    "football_basketball": "Football & basketball", "table_tennis": "Table tennis paddles",
    "iron": "Iron", "sewing_machine": "Sewing machine", "volleyball_set": "Beach volleyball set",
    "foldable_chairs_table": "Foldable chairs & table", "carpet_cleaner": "Carpet shampoo/cleaner",
    "pressure_washer": "Pressure washer", "party_tent": "Party tent",
}
ITEM_ORDER = list(ITEM_LABELS)
ITEM_VOLUME_M3 = {
    "vacuum_cleaner": .06, "steam_cleaner": .08, "drill": .004, "video_projector": .006,
    "hand_sander": .004, "fitness_equipment": .05, "football_basketball": .008,
    "table_tennis": .005, "iron": .004, "sewing_machine": .03, "volleyball_set": .01,
    "foldable_chairs_table": .25, "carpet_cleaner": .10, "pressure_washer": .08, "party_tent": .12,
}
ITEM_VALUE_EUR = {
    "vacuum_cleaner": 160, "steam_cleaner": 140, "drill": 110, "video_projector": 280,
    "hand_sander": 70, "fitness_equipment": 50, "football_basketball": 30,
    "table_tennis": 40, "iron": 50, "sewing_machine": 180, "volleyball_set": 30,
    "foldable_chairs_table": 165, "carpet_cleaner": 230, "pressure_washer": 160, "party_tent": 180,
}
INITIATIVES = [("secondhand","Second-hand shops"),("sharing","Sharing initiatives"),
               ("renting","Renting initiatives"),("repair","Repair shops")]


def pct(x): return 100 * x

def income3(x):
    if pd.isna(x): return np.nan
    s = str(x).lower()
    if "below" in s: return "Below median"
    if "around" in s: return "Around median"
    if "above" in s: return "Above median"
    return np.nan


def under_flag(own, freq, city):
    """Report definition: owner and never/less-than-monthly (freq <=2).
    Bergen follows the documented conservative rule: missing owner frequency = underutilised.
    Other cities: missing frequency is excluded from underutilisation denominator.
    """
    own = pd.to_numeric(own, errors="coerce")
    freq = pd.to_numeric(freq, errors="coerce")
    out = pd.Series(np.nan, index=own.index, dtype=float)
    m = own.eq(1)
    out.loc[m & freq.notna()] = (freq.loc[m & freq.notna()] <= 2).astype(float)
    # The final report analysis uses the conservative missing rule for all cities.
    out.loc[m & freq.isna()] = 1.0
    return out


def item_metrics(df, city):
    rows=[]; n=len(df); H=CITY_HOUSEHOLDS[city]
    for slug in ITEM_ORDER:
        oc=f"own__{slug}"; fc=f"usefreq__{slug}"; rc=f"rent__{slug}"
        if oc not in df.columns or pd.to_numeric(df[oc], errors='coerce').notna().sum()==0: continue
        own=pd.to_numeric(df[oc], errors='coerce'); freq=pd.to_numeric(df.get(fc), errors='coerce') if fc in df else pd.Series(np.nan,index=df.index)
        rent=pd.to_numeric(df.get(rc), errors='coerce') if rc in df else pd.Series(np.nan,index=df.index)
        owners=int(own.fillna(0).sum()); ownership=owners/n
        under=under_flag(own,freq,city); vals=under[own.eq(1)].dropna()
        under_n=int(vals.eq(1).sum()); under_rate=vals.mean() if len(vals) else np.nan
        borrow=rent.eq(1).mean() if rent.notna().any() else np.nan
        suitability=ownership*under_rate if pd.notna(under_rate) else np.nan
        spi=np.sqrt(suitability*borrow) if pd.notna(suitability) and pd.notna(borrow) else np.nan
        est_owned=ownership*H; est_under=suitability*H if pd.notna(suitability) else np.nan
        rows.append({"City":city,"Item":ITEM_LABELS[slug],"Item_slug":slug,"Respondents (n)":n,
          "Owners (n)":owners,"Ownership (%)":pct(ownership),"Underutilised owners (n)":under_n,
          "Underutilisation (%)":pct(under_rate) if pd.notna(under_rate) else np.nan,
          "Borrowing willingness (%)":pct(borrow) if pd.notna(borrow) else np.nan,
          "Suitability (%)":pct(suitability) if pd.notna(suitability) else np.nan,
          "Sharing potential index":pct(spi) if pd.notna(spi) else np.nan,
          "Estimated owned items":est_owned,"Estimated underutilised items":est_under,
          "Estimated storage volume (m³)":est_under*ITEM_VOLUME_M3[slug] if pd.notna(est_under) else np.nan,
          "Estimated value (€)":est_under*ITEM_VALUE_EUR[slug] if pd.notna(est_under) else np.nan})
    return pd.DataFrame(rows)


def bootstrap_ci(df, city, metric, B=1000, seed=42):
    rng=np.random.default_rng(seed); vals={slug:[] for slug in ITEM_ORDER}
    for _ in range(B):
        b=df.iloc[rng.integers(0,len(df),len(df))]
        m=item_metrics(b,city).set_index('Item_slug')
        for slug in vals:
            if slug in m.index and metric in m: vals[slug].append(m.loc[slug,metric])
    return {slug:(np.nanpercentile(v,2.5),np.nanpercentile(v,97.5)) for slug,v in vals.items() if len(v)}


def plot_city_comparison(master, metric, ylabel, filename):
    piv=master.pivot(index='Item',columns='City',values=metric)
    order=(master.groupby('Item')[metric].mean().sort_values(ascending=False)).index
    piv=piv.reindex(order); cities=list(CITY_FILES)
    x=np.arange(len(piv)); width=.12
    fig,ax=plt.subplots(figsize=(14,6.5))
    for i,c in enumerate(cities):
        if c not in piv: continue
        ax.bar(x+(i-(len(cities)-1)/2)*width,piv[c].values,width,label=c)
    ax.set_xticks(x); ax.set_xticklabels(piv.index,rotation=40,ha='right')
    ax.set_ylabel(ylabel); ax.legend(ncol=3,fontsize=8); ax.grid(axis='y',alpha=.2)
    fig.tight_layout(); fig.savefig(FIGURES/filename,dpi=300,bbox_inches='tight'); plt.close(fig)


def initiative_table(df,city):
    rows=[]
    for key,label in INITIATIVES:
        know=pd.to_numeric(df.get(f'know__{key}'),errors='coerce').fillna(0)
        use=pd.to_numeric(df.get(f'use__{key}'),errors='coerce').fillna(0)
        # Survey allowed use without separately ticking know; analytically, use implies awareness.
        aware=((know.eq(1)) | (use.eq(1)))
        using=use.eq(1); aware_not=aware & ~using; unknown=~aware
        rows.append({"City":city,"Initiative":label,"Know (%)":pct(aware.mean()),"Use (%)":pct(using.mean()),
                     "Know but don't use (%)":pct(aware_not.mean()),"Don't know (%)":pct(unknown.mean())})
    return pd.DataFrame(rows)


def reasons_table(dfs, prefix, borrowed_value):
    city_tables=[]
    all_cols=sorted(set().union(*[{c for c in d.columns if c.startswith(prefix)} for d in dfs.values()]))
    for col in all_cols:
        label=col.split('__',1)[1].replace('_',' ').replace('dont',"don't").capitalize()
        row={'Reason':label}; pooled_num=pooled_den=0
        for city,df in dfs.items():
            b=df['borrowed_sharing_station'].astype(str).str.lower().eq(borrowed_value)
            s=pd.to_numeric(df[col],errors='coerce') if col in df else pd.Series(np.nan,index=df.index)
            den=int(b.sum()); num=int(s[b].fillna(0).eq(1).sum())
            row[city]=100*num/den if den else np.nan; pooled_num+=num; pooled_den+=den
        row['Overall']=100*pooled_num/pooled_den if pooled_den else np.nan; city_tables.append(row)
    return pd.DataFrame(city_tables).sort_values('Overall',ascending=False)


def respondent_item_long(dfs):
    rows=[]
    for city,df in dfs.items():
        temp=df.copy(); temp['income_group']=temp['income'].map(income3)
        # stable respondent cluster id across cities
        idcol=next((c for c in ['Id','ID','response_id'] if c in temp.columns),None)
        rid=(temp[idcol].astype(str) if idcol else temp.index.astype(str))
        for slug in ITEM_ORDER:
            oc=f'own__{slug}'; fc=f'usefreq__{slug}'
            if oc not in temp or pd.to_numeric(temp[oc],errors='coerce').notna().sum()==0: continue
            own=pd.to_numeric(temp[oc],errors='coerce'); under=under_flag(own,pd.to_numeric(temp.get(fc),errors='coerce') if fc in temp else pd.Series(np.nan,index=temp.index),city)
            part=pd.DataFrame({'cluster':city+'_'+rid,'city':city,'item':ITEM_LABELS[slug],'ownership':own,'underutilisation':under,
                               'income_group':temp['income_group'],'age':temp['age'],'gender':temp['gender'],'education':temp['education']})
            rows.append(part)
    return pd.concat(rows,ignore_index=True)


def fit_gee(long,outcome):
    d=long.copy()
    if outcome=='underutilisation':
        # Restrict to city-item cells with at least 10 owners, matching the final report.
        owner_counts=(d[d.ownership.eq(1)].groupby(['city','item']).size().rename('owners').reset_index())
        keep=owner_counts.loc[owner_counts.owners>=10,['city','item']]
        d=d.merge(keep,on=['city','item'],how='inner')
        d=d[d.ownership.eq(1)]
    d=d.dropna(subset=[outcome,'income_group','age','gender','education','city','item','cluster']).copy()
    # Explicit reference categories to match report.
    formula=(f"{outcome} ~ C(income_group, Treatment(reference='Above median')) + "
             "C(age, Treatment(reference='18–25')) + C(gender, Treatment(reference='Man')) + "
             "C(education, Treatment(reference='Doctorate / PhD')) + C(city) + C(item)")
    model=smf.gee(formula,groups='cluster',data=d,family=sm.families.Binomial(),cov_struct=sm.cov_struct.Exchangeable()).fit()
    return model,d


def extract_demographic_results(own_model,under_model):
    def get(model,prefix,label):
        out=[]
        for name,b in model.params.items():
            if prefix not in name: continue
            level=name.split('[T.',1)[-1].rstrip(']')
            se=model.bse[name]; OR=np.exp(b); lo=np.exp(b-1.96*se); hi=np.exp(b+1.96*se); p=model.pvalues[name]
            out.append((label,level,OR,lo,hi,p))
        return out
    blocks=[("Income","C(income_group",'Above median'),("Age","C(age",'18–25'),("Gender","C(gender",'Man'),("Education","C(education",'Doctorate / PhD')]
    rows=[]
    for label,prefix,ref in blocks:
        od={x[1]:x[2:] for x in get(own_model,prefix,label)}; ud={x[1]:x[2:] for x in get(under_model,prefix,label)}
        levels=[]
        for k in list(od)+list(ud):
            if k not in levels: levels.append(k)
        for level in levels:
            o=od.get(level,(np.nan,)*4); u=ud.get(level,(np.nan,)*4)
            rows.append({'Predictor':label,'Category':level,'Reference':ref,
                         'Ownership OR':o[0],'Ownership CI low':o[1],'Ownership CI high':o[2],'Ownership p-value':o[3],
                         'Underutilisation OR':u[0],'Underutilisation CI low':u[1],'Underutilisation CI high':u[2],'Underutilisation p-value':u[3]})
    return pd.DataFrame(rows)


def adjusted_income_probabilities(model, data, outcome):
    """Average adjusted probabilities with robust delta-method 95% CIs."""
    design_info=model.model.data.design_info
    params=np.asarray(model.params,dtype=float); cov=np.asarray(model.cov_params(),dtype=float)
    z=float(norm.ppf(.975)); rows=[]
    for cat in ['Below median','Around median','Above median']:
        new=data.copy(); new['income_group']=cat
        pred=np.asarray(model.predict(new),dtype=float); adj=float(np.mean(pred))
        X=np.asarray(build_design_matrices([design_info],new,return_type='dataframe')[0],dtype=float)
        p=expit(X@params); grad=np.mean((p*(1-p))[:,None]*X,axis=0)
        se=float(np.sqrt(max(float(grad@cov@grad),0)))
        lo=max(0,adj-z*se); hi=min(1,adj+z*se)
        rows.append({'category':cat,'adjusted_probability':adj,'robust_se_probability':se,
                     'ci_low_95':lo,'ci_high_95':hi,'adjusted_percentage':100*adj,
                     'ci_low_95_percentage':100*lo,'ci_high_95_percentage':100*hi})
    return pd.DataFrame(rows)

def plot_adjusted(tab,outcome,filename):
    fig,ax=plt.subplots(figsize=(8,5.5)); x=np.arange(len(tab)); y=tab.adjusted_percentage.values
    lo=tab.ci_low_95_percentage.values; hi=tab.ci_high_95_percentage.values
    ax.errorbar(x,y,yerr=np.vstack([y-lo,hi-y]),fmt='o',markersize=8,capsize=5,linewidth=1.5)
    ax.set_xticks(x); ax.set_xticklabels(tab.category)
    ax.set_ylabel(f'Adjusted probability of {outcome} (%)'); ax.set_xlabel('Household income relative to city median')
    ymin=max(0,np.nanmin(lo)-4); ymax=min(100,np.nanmax(hi)+8); ax.set_ylim(ymin,ymax)
    for i,v in enumerate(y): ax.annotate(f'{v:.1f}%\n95% CI {lo[i]:.1f}–{hi[i]:.1f}%',(i,v),xytext=(0,14),textcoords='offset points',ha='center',fontsize=9)
    ax.grid(axis='y',alpha=.25); fig.tight_layout(); fig.savefig(FIGURES/filename,dpi=300,bbox_inches='tight'); plt.close(fig)

def main():
    dfs={city:pd.read_csv(path) for city,path in CITY_FILES.items()}
    # core item master table
    master=pd.concat([item_metrics(df,city) for city,df in dfs.items()],ignore_index=True)
    master.to_csv(TABLES/'city_item_master_table.csv',index=False)
    avg=(master.groupby('Item',as_index=False).agg(**{'Mean ownership (%)':('Ownership (%)','mean'),
        'Mean underutilisation (%)':('Underutilisation (%)','mean'),'Cities included':('Underutilisation (%)','count')}))
    avg=avg.sort_values('Mean underutilisation (%)',ascending=False); avg.to_csv(TABLES/'table_mean_ownership_underutilisation.csv',index=False)
    plot_city_comparison(master,'Ownership (%)','Ownership (%)','figure_ownership_by_city.png')
    plot_city_comparison(master,'Underutilisation (%)','Underutilisation among owners (%)','figure_underutilisation_by_city.png')
    plot_city_comparison(master,'Sharing potential index','Sharing potential index','figure_sharing_potential_by_city.png')

    # initiative adoption
    adoption=pd.concat([initiative_table(df,c) for c,df in dfs.items()],ignore_index=True)
    adoption.to_csv(TABLES/'table_initiative_adoption.csv',index=False)

    # sharing-station motivations/barriers
    reasons_table(dfs,'reason_yes__','yes').to_csv(TABLES/'table_reasons_borrowing.csv',index=False)
    reasons_table(dfs,'reason_no__','no').to_csv(TABLES/'table_reasons_not_borrowing.csv',index=False)

    # demographics and GEE
    long=respondent_item_long(dfs); long.to_csv(TABLES/'respondent_item_analysis_dataset.csv',index=False)
    own_model,own_d=fit_gee(long,'ownership'); under_model,under_d=fit_gee(long,'underutilisation')
    dem=extract_demographic_results(own_model,under_model); dem.to_csv(TABLES/'table_GEE_demographics.csv',index=False)
    own_adj=adjusted_income_probabilities(own_model,own_d,'ownership'); under_adj=adjusted_income_probabilities(under_model,under_d,'underutilisation')
    own_adj.to_csv(TABLES/'adjusted_ownership_by_income.csv',index=False); under_adj.to_csv(TABLES/'adjusted_underutilisation_by_income.csv',index=False)
    plot_adjusted(own_adj,'ownership','figure_adjusted_ownership_by_income.png'); plot_adjusted(under_adj,'underutilisation','figure_adjusted_underutilisation_by_income.png')

    # QA summary used to verify report headline values
    qa=pd.DataFrame({
      'Check':['Total respondents','Ownership model rows','Underutilisation model rows','Mean drill ownership (%)','Mean drill underutilisation (%)'],
      'Value':[sum(len(d) for d in dfs.values()),len(own_d),len(under_d),
               avg.loc[avg.Item.eq('Drill'),'Mean ownership (%)'].iloc[0],avg.loc[avg.Item.eq('Drill'),'Mean underutilisation (%)'].iloc[0]]})
    qa.to_csv(TABLES/'QA_report_checks.csv',index=False)
    print('Report outputs written to:',OUT)
    print(qa.to_string(index=False))

if __name__=='__main__':
    main()
