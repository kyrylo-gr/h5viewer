def get_aqm_variable(code):
    code2 = code[:code.find('.analysis_cell')]
    return code2[code2.rfind('\n')+1:]


def convert_analyse_code(code: str, filepath: str):
    aqm_variable = get_aqm_variable(code)
    return (code
            .replace('%', '#%')
            .replace("fig.show()", "plt.show()")
            .replace(f"{aqm_variable}.analysis_cell(", f'{aqm_variable}.analysis_cell(filepath="{filepath}",')
            .replace(f"{aqm_variable}.save_fig(", f"# {aqm_variable}.save_fig(")
            )
