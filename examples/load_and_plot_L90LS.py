from pathlib import Path
import subprocess
import sys

import pylsuq as lsuq
import webbrowser

output_dir = Path(__file__).parent / "output"
xml_path = output_dir / "L90LS_UD_OS_OS_UQ.xml"

if not xml_path.is_file():
    generator_path = Path(__file__).with_name("spec_of_L90LS.py")
    subprocess.run([sys.executable, str(generator_path)], check=True)

# Load a lsuq xml file and print domains
lsuq_file = lsuq.load_xml(xml_path)
plot_axes = [("pA","pB"),("uA","pB")]

for ia,sub_axes in enumerate(plot_axes):
    for id,domain in enumerate(lsuq_file.domains.typed_operational_domains+lsuq_file.domains.activity_domains):
        if id == 0:
            fig= lsuq.add_domain_plot(domain, plot_axes = sub_axes)
        else:
            lsuq.add_domain_plot(domain, plot_axes = sub_axes, fig=fig)

    html_path = output_dir / Path( "domains_L90LS_UD_OS_OS_UQ_" + str(ia) + ".html")
    fig.write_html(html_path) 
    webbrowser.open(html_path.resolve().as_uri())