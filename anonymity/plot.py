import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_mondrian(df, df_k_anonym):
    fig, ax = plt.subplots(figsize=(20, 10))
    df_plot = df\
                .groupby(['age', 'code_postal'])\
                .size()\
                .to_frame()\
                .reset_index()\
                .rename(columns={0: 'n_patients'})

    sc = ax.scatter(x=df_plot.age, y=df_plot.code_postal, s=15, c=df_plot.n_patients, cmap='hot')

    for (age, code_postal), dfx in df_k_anonym.groupby(['age', 'code_postal']):
        if '-' in str(age):
            age_min, age_max = map(int, age.split('-'))
        else:
            age = int(age)
            age_min, age_max = age, age

        age_min -= 0.5
        age_max += 0.5

        if '-' in str(code_postal):
            code_postal_min, code_postal_max = map(lambda x: int(x), code_postal.split('-'))
            code_postal_jitter = .5
        else:
            code_postal = int(code_postal)
            code_postal_min, code_postal_max  = code_postal, code_postal
            code_postal_jitter = .01 * (code_postal - 69000)
        
        code_postal_min -= code_postal_jitter
        code_postal_max += code_postal_jitter

        rect = ax.add_patch(
        patches.Rectangle(
            (age_min, code_postal_min),
            age_max - age_min,
            code_postal_max - code_postal_min,
            facecolor = 'red',
            edgecolor='red',
            fill=True,
            alpha=0.2
         ) )

    fig.colorbar(sc, ax=ax)