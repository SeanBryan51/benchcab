#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File: offline_metrics.py
Author: naught101
Email: naught101@email.com
Github: https://git.nci.org.au/nnh561/cable_testing
Description: Compares two simulations against an output dataset.

Usage:
    offline_metrics.py calculate <sim_file> <obs_file> [--out=<out_file>] [--name=<name>] [--print]
    offline_metrics.py compare <name> <metrics_file> <baseline_name> <baseline_file>
    offline_metrics.py plot <metrics_file> <out_file>
    offline_metrics.py xml -u <build_url> -o <out_file> <image_file>...
    offline_metrics.py (-h | --help | --version)

Options:
    -h, --help    Show this screen and exit.
"""

from docopt import docopt

import os
import numpy as np
import scipy.stats as ss
import pandas as pd
import xarray as xr
from datetime import datetime as dt
from collections import OrderedDict

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


# Metrics
# Assume x=obs, y=sim
metrics = OrderedDict()
metrics['rmse'] = dict(
    name='root mean squared error',
    func=lambda x, y: np.sqrt(np.mean((y - x) ** 2)),
    best='zero')
metrics['mbe'] = dict(
    name='mean bias',
    func=lambda x, y: np.mean(y - x),
    best='zero')
metrics['corr'] = dict(
    name='correlation coefficient',
    func=lambda x, y: np.corrcoef(y, x)[0, 1],
    best='one')
metrics['sd_diff'] = dict(
    name='standard deviation error',
    func=lambda x, y: np.std(y) / np.std(x),
    best='one')
metrics['nme'] = dict(
    name='normalised mean error',
    func=lambda x, y: np.sum(np.abs(y - x)) / np.sum(np.abs(np.mean(x) - x)),
    best='zero')
metrics['5th%'] = dict(
    name='5th percentile difference',
    func=lambda x, y: (np.percentile(y, 5) - np.percentile(x, 5)),
    best='zero')
metrics['95th%'] = dict(
    name='95th percentile difference',
    func=lambda x, y: (np.percentile(y, 95) - np.percentile(x, 95)),
    best='zero')
metrics['skewness'] = dict(
    name='skewness error',
    func=lambda x, y: ss.skew(y) / ss.skew(x),
    best='one')
metrics['kurtosis'] = dict(
    name='kurtosis error',
    func=lambda x, y: ss.kurtosis(y) / ss.kurtosis(x),
    best='one')
metrics['overlap'] = dict(
    name='pdf overlap',
    func=lambda x, y: np.sum(np.fmin(np.histogram(y, bins=100, density=True)[0],
                                     np.histogram(x, bins=100, density=True)[0])),
    best='one')


flux_vars = ['Qh', 'Qle', 'Rnet', 'NEE', 'Qg']


def run_all_metrics(sim_ds, obs_ds):
    """Run a bunch of standard metrics against obs for each variable"""

    records = []
    for v in flux_vars:

        if v in sim_ds and v in obs_ds:

            for m in metrics:
                fn = metrics[m]['func']

                records.append(dict(var=v, metric=m,
                                    value=fn(obs_ds[v].values.ravel(), sim_ds[v].values.ravel())
                                    ))
    results = pd.DataFrame(records)

    return results[['var', 'metric', 'value']]


def calculate_metrics(sim_file, obs_file, out_file=None, name=None,
                      display=False):
    """Calculate metrics and save them to output file """
    sim_ds = xr.open_dataset(sim_file)
    obs_ds = xr.open_dataset(obs_file)

    assert obs_ds.dims['time'] == sim_ds.dims['time'], "Incorrect number of timesteps in simulation!"

    results = run_all_metrics(sim_ds, obs_ds)

    if name:
        results['site'] = name

    sim_ds.close()
    obs_ds.close()

    if out_file is not None:
        if out_file.endswith('.csv'):
            results.to_csv(out_file)
        elif out_file.endswith('.html'):
            results.to_html(out_file)

    if display:
        print(results)

    return


def compare_metrics(name, metric_file, baseline_name, baseline_file):
    """Normalises metrics relative to the baseline

    :metric_file: Metrics CSV, as generated by the calculate function
    :baseline_file: Baseline metrics file with shich to compare the metrics
    :returns: TODO
    """
    metric_df = pd.DataFrame.from_csv(metric_file)
    baseline = pd.DataFrame.from_csv(baseline_file)

    if 'site' in metric_df.columns:
        index_cols = ['var', 'metric', 'site']
    else:
        index_cols = ['var', 'metric']

    metric_df.set_index(index_cols, inplace=True)
    baseline.set_index(index_cols, inplace=True)

    one_metrics = [m for m in metrics if metrics[m]['best'] == 'one']
    zero_metrics = [m for m in metrics if metrics[m]['best'] == 'zero']

    # TODO: currently assumes that all rows correspond. Is that safe?

    # normalise metric results, so all metrics are positive, lower is better
    for df in [metric_df, baseline]:
        ones_index = df.index.get_level_values('metric').isin(one_metrics)
        df['value'][ones_index] = np.abs(1 - df['value'][ones_index])

        zeros_index = df.index.get_level_values('metric').isin(zero_metrics)
        df['value'][zeros_index] = np.abs(df['value'][zeros_index])

    # divide metrics by baseline (e.g. branch by trunk)
    if 'site' in index_cols:
        baseline_mean = baseline.groupby(level=['var', 'metric']).mean()
        results = {}
        for site in metric_df.index.get_level_values('site'):
            results[site] = metric_df.xs(site, level='site') / baseline_mean
        results = pd.concat(results, names=['site'])
    else:
        results = metric_df / baseline

    results = results.rename(columns={'value': name})
    results[baseline_name] = 1

    results.to_csv('normalised_metrics.csv')

    return


def plot_metrics(filename, out_file):
    """plots metrics facetted by variable"

    :filename: metrics csv with var, metrics columns, and values columns per model
    """
    df = pd.read_csv(filename)
    df['metric'] = pd.Categorical(df['metric'], df['metric'].unique())
    if 'site' in df.columns:
        index_cols = ['var', 'metric', 'site']
        df.set_index(index_cols, inplace=True)
    else:
        index_cols = ['var', 'metric']
        df.set_index(index_cols, inplace=True)

    mean_df = df.groupby(level=['var', 'metric']).mean()

    flux_vars = list(df.index.levels[0])
    n_vars = len(flux_vars)
    metric_names = list(df.index.levels[1])
    n_metrics = len(metrics)

    fig, axes = plt.subplots(n_vars, sharex=True, sharey=True, figsize=(10, 12))

    for i in range(n_vars):
        v = flux_vars[i]
        # The AxesGrid object work as a list of axes.
        # TODO: hardcoded use of first column in scatter- might not always want this.
        y_vals = df.xs(v).values[:, 0]
        var_sites = int(len(y_vals) / n_metrics)
        axes[i].scatter(x=list(range(n_metrics)) * var_sites, y=y_vals, label=df.columns)
        axes[i].plot(mean_df.xs(v).values, label=df.columns)
        axes[i].text(0.03, 0.1, '%s sites' % var_sites, transform=axes[i].transAxes)

        axes[i].set_xlim([-0.5, n_metrics - 0.5])
        axes[i].set_xticks(list(range(n_metrics)))
        axes[i].set_xticklabels(metric_names)
        axes[i].set_ylim([0.5, 1.5])
        axes[i].set_ylabel(v)

    axes[0].legend(df.columns, fontsize='x-small')

    suptitle_tpl = '{0} metrics normalised by {1} mean at PLUMBER sites\n' + \
        'lower is better - dots: site values, lines: mean over sites\n' + \
        'produced on {t}'
    fig.suptitle(suptitle_tpl.format(*df.columns, t=dt.now().isoformat()[0:19]))

    plt.savefig(out_file, dpi=75)


def generate_xml(build_url, image_files, out_file):
    """generates XML for use with the Jenkins Summary Display Plugin

    :image_file: image file name
    :out_file: xml file to write to
    """

    image_url_tpl = "{bu}/artifact/{i}"
    image_filenames = [os.path.basename(i) for i in image_files]
    image_urls = [image_url_tpl.format(bu=build_url, i=i) for i in image_files]

    image_row_tpl = """                <tr><td>
        {fn}:<br />
        <![CDATA[
            <img src="{u}" />
        ]]>
    </td></tr>"""
    image_rows = "\n".join([image_row_tpl.format(fn=ifn, u=iu) for ifn, iu in zip(image_filenames, image_urls)])

    xml = """<section name="Branch/Trunk comparison">
    <table border="0">\
            {rows}
            </table>
</section>
""".format(rows=image_rows)

    with open(out_file, "w") as f:
        f.writelines(xml)

    return


def main(args):

    if args['calculate']:
        calculate_metrics(args['<sim_file>'], args['<obs_file>'],
                          args['--out'], args['--name'], args['--print'])
    if args['compare']:
        compare_metrics(args['<name>'], args['<metrics_file>'], args['<baseline_name>'], args['<baseline_file>'])
    if args['plot']:
        plot_metrics(args['<metrics_file>'], args['<out_file>'])
    if args['xml']:
        generate_xml(args['<build_url>'], args['<image_file>'], args['<out_file>'])

    return


if __name__ == '__main__':
    args = docopt(__doc__)

    main(args)
