from datetime import date

import pandas as pd
import streamlit as st

from data.config import MES_EXPORT_COLUMNS, VALID_SLITTERS, VALID_SLITTING_TEAMS
from logic.allocation import allocate_master_rolls, validate_allocation
from logic.batch import generate_batch
from logic.export_excel import build_mes_dataframe, export_mes_excel
from logic.production import ProductionPlan, calculate_production_plan
from logic.validation import validate_generated_batch, validate_master_rolls


st.set_page_config(page_title="Slitting Barcode Assistant", layout="wide")


def show_errors(errors: list[str]) -> None:
    for error in errors:
        st.error(error)


def plan_to_dataframe(plan: ProductionPlan) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Item": "Shipment Requirement", "Value": plan.shipment_qty},
            {"Item": "Target Yield", "Value": f"{plan.yield_percent:g}%"},
            {"Item": "Required Production Qty", "Value": plan.required_production_qty},
            {"Item": "Small Rolls / Cut", "Value": plan.planning_small_rolls_per_cut},
            {"Item": "Required Master Rolls", "Value": plan.required_master_rolls},
            {"Item": "Planned Small Rolls", "Value": plan.planned_small_rolls},
            {"Item": "Expected Good Rolls", "Value": plan.expected_good_rolls},
        ]
    )


def get_plan(
    product_width_mm: float | None,
    shipment_qty: int | None,
    yield_percent: float,
    rolls_per_cut: int,
) -> ProductionPlan | None:
    if product_width_mm is None:
        st.error("Product Width is required.")
        return None
    if product_width_mm <= 0:
        st.error("Product Width must be greater than 0.")
        return None
    if shipment_qty is None:
        st.error("Shipment Qty is required.")
        return None
    try:
        return calculate_production_plan(shipment_qty, yield_percent, rolls_per_cut)
    except ValueError as exc:
        st.error(str(exc))
        return None


st.title("Slitting Barcode Assistant")
st.caption("Deterministic V1 generator for MES Excel upload data.")

st.header("1. Production Input")
with st.container(border=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        product_width_mm = st.number_input(
            "Product Width (mm)",
            min_value=0.01,
            step=0.01,
            value=None,
            placeholder="Enter width",
        )
    with col2:
        shipment_qty = st.number_input(
            "Shipment Qty",
            min_value=1,
            step=1,
            value=None,
            placeholder="Enter qty",
        )
    with col3:
        yield_percent = st.number_input("Target Yield %", min_value=0.01, max_value=100.0, step=0.5, value=85.0)
    with col4:
        rolls_per_cut = st.number_input("Planning Small Rolls per Cut", min_value=1, step=1, value=10)

    calculate_clicked = st.button("Calculate Production Plan", type="primary")

plan = None
if calculate_clicked:
        st.session_state["plan_calculated"] = True

if st.session_state.get("plan_calculated", False):
    plan = get_plan(
        None if product_width_mm is None else float(product_width_mm),
        None if shipment_qty is None else int(shipment_qty),
        float(yield_percent),
        int(rolls_per_cut),
    )

if plan is not None:
    st.header("2. Production Plan")
    st.dataframe(plan_to_dataframe(plan), hide_index=True, use_container_width=True)
    st.success(
        f"Required Master Rolls: {plan.required_master_rolls}; "
        f"Planned Small Rolls: {plan.planned_small_rolls}"
    )

    st.header("3. Machine Allocation")
    if "applied_slitters" not in st.session_state:
        st.session_state["applied_slitters"] = ["FX1", "FX2", "FX3"]
    if "pending_slitters" not in st.session_state:
        st.session_state["pending_slitters"] = st.session_state["applied_slitters"]

    with st.form("machine_selection_form"):
        st.multiselect(
            "Selected Slitters",
            list(VALID_SLITTERS),
            key="pending_slitters",
        )
        apply_machine_selection = st.form_submit_button("Apply Machine Selection", type="primary")

    if apply_machine_selection:
        pending_slitters = st.session_state["pending_slitters"]
        if not pending_slitters:
            st.error("At least one slitter must be selected.")
        else:
            st.session_state["applied_slitters"] = pending_slitters
            default_allocation = allocate_master_rolls(plan.required_master_rolls, pending_slitters)
            for slitter in VALID_SLITTERS:
                if slitter not in pending_slitters:
                    st.session_state.pop(f"allocation_{slitter}", None)
            for slitter, value in default_allocation.items():
                st.session_state[f"allocation_{slitter}"] = value
            st.session_state["allocation_plan_master_rolls"] = plan.required_master_rolls
            st.success("Machine selection applied.")

    selected_slitters = st.session_state["applied_slitters"]

    should_reset_allocation = (
        st.session_state.get("allocation_plan_master_rolls") != plan.required_master_rolls
        or any(f"allocation_{slitter}" not in st.session_state for slitter in selected_slitters)
    )
    if should_reset_allocation:
        default_allocation = allocate_master_rolls(plan.required_master_rolls, selected_slitters)
        for slitter, value in default_allocation.items():
            st.session_state[f"allocation_{slitter}"] = value
        st.session_state["allocation_plan_master_rolls"] = plan.required_master_rolls

    st.caption(f"Applied slitters: {', '.join(selected_slitters)}")
    allocation: dict[str, int] = {}
    allocation_cols = st.columns(len(selected_slitters))
    for index, slitter in enumerate(selected_slitters):
        with allocation_cols[index]:
            allocation[slitter] = int(
                st.number_input(
                    slitter,
                    min_value=0,
                    step=1,
                    key=f"allocation_{slitter}",
                )
            )

    allocation_errors = validate_allocation(plan.required_master_rolls, allocation)
    allocated_total = sum(allocation.values())
    if allocation_errors:
        show_errors(allocation_errors)
    else:
        st.success(f"Allocation valid: {allocated_total} / {plan.required_master_rolls} Master Rolls allocated.")

    st.header("4. Master Roll Input")
    st.write(f"Required Master Rolls: **{plan.required_master_rolls}**")
    master_roll_text = st.text_area(
        "Paste Master Roll SNs, one per line",
        height=180,
        placeholder="ULE3U1B260824UA011\nULE3U1B260824UA012\nULE3U1B260824UA013",
        key="master_roll_text",
    )
    apply_master_rolls = st.button("Apply Master Rolls", type="primary", key="apply_master_rolls")
    parsed_master_rolls, mr_errors = validate_master_rolls(master_roll_text, plan.required_master_rolls)
    unique_entered = len({roll.sn for roll in parsed_master_rolls})
    master_roll_inputs = (master_roll_text, plan.required_master_rolls)
    if st.session_state.get("applied_master_roll_inputs") != master_roll_inputs:
        st.session_state.pop("applied_master_roll_inputs", None)
    if apply_master_rolls and not mr_errors and parsed_master_rolls:
        st.session_state["applied_master_roll_inputs"] = master_roll_inputs
    master_rolls_applied = st.session_state.get("applied_master_roll_inputs") == master_roll_inputs

    if apply_master_rolls and mr_errors:
        st.warning(f"Entered: {unique_entered} / {plan.required_master_rolls}")
        show_errors(mr_errors)
    elif not master_roll_text.strip():
        st.info("Enter Master Roll SNs to continue.")
    elif master_rolls_applied:
        st.success(f"{unique_entered} / {plan.required_master_rolls} Master Rolls applied")
    else:
        st.warning("Master Rolls not applied.")

    st.header("5. Slitting Parameters")
    col1, col2, col3 = st.columns(3)
    with col1:
        slitting_date = st.date_input("Slitting Date", value=date.today())
    with col2:
        slitting_team = st.selectbox("Slitting Team", list(VALID_SLITTING_TEAMS))
    with col3:
        starting_sequence = int(st.number_input("Starting Slitting Sequence", min_value=0, max_value=99999, step=1, value=1))

    generate_clicked = st.button(
        "Generate 生成",
        type="primary",
        disabled=bool(allocation_errors or mr_errors or not parsed_master_rolls or not master_rolls_applied),
        key="generate_batch",
    )

    generated_rows: list[dict[str, str | int]] = []
    edited_assignments = pd.DataFrame()

    if not allocation_errors and not mr_errors and parsed_master_rolls and master_rolls_applied:
        assignments: list[str] = []
        for slitter, count in allocation.items():
            assignments.extend([slitter] * count)

        assignment_rows = [
            {
                "Order": index + 1,
                "Master Roll SN": roll.sn,
                "Assigned Slitter": assignments[index],
                "Actual Small Roll Qty": int(rolls_per_cut),
            }
            for index, roll in enumerate(parsed_master_rolls)
        ]

        st.header("6. Generate")
        edited_assignments = st.data_editor(
            pd.DataFrame(assignment_rows),
            hide_index=True,
            use_container_width=True,
            disabled=["Order", "Master Roll SN", "Assigned Slitter"],
            column_config={
                "Actual Small Roll Qty": st.column_config.NumberColumn(
                    min_value=1,
                    step=1,
                    required=True,
                )
            },
        )

        actual_qty_by_master_roll = {
            str(row["Master Roll SN"]): int(row["Actual Small Roll Qty"])
            for row in edited_assignments.to_dict("records")
        }

        generation_inputs = (
            tuple(MES_EXPORT_COLUMNS),
            product_width_mm,
            shipment_qty,
            yield_percent,
            rolls_per_cut,
            tuple(allocation.items()),
            tuple(actual_qty_by_master_roll.items()),
            slitting_date,
            slitting_team,
            starting_sequence,
        )
        result = st.session_state.get("generated_result")
        if result is not None and result["inputs"] != generation_inputs:
            st.session_state.pop("generated_result", None)
            result = None

        validation_errors: list[str] = []
        if generate_clicked:
            st.session_state.pop("generated_result", None)
            result = None
            try:
                generated_rows = generate_batch(
                    product_width_mm=float(product_width_mm),
                    parsed_master_rolls=parsed_master_rolls,
                    allocation=allocation,
                    actual_qty_by_master_roll=actual_qty_by_master_roll,
                    slitting_date=slitting_date,
                    slitting_team=slitting_team,
                    starting_sequence=starting_sequence,
                )
                validation_errors = validate_generated_batch(generated_rows)
                if not validation_errors:
                    result = {
                        "inputs": generation_inputs,
                        "rows": generated_rows,
                        "excel": export_mes_excel(generated_rows),
                    }
                    st.session_state["generated_result"] = result
            except ValueError as exc:
                validation_errors.append(str(exc))

        if result is None and not validation_errors:
            st.stop()

        st.header("7. Validate")
        if validation_errors:
            show_errors(validation_errors)
        else:
            generated_rows = result["rows"]
            st.success("Validation Passed")

            total_actual = len(generated_rows)
            ending_sequence = starting_sequence + total_actual - 1 if total_actual else starting_sequence
            next_sequence = starting_sequence + total_actual

            summary = pd.DataFrame(
                [
                    {"Item": "Product Width", "Value": f"{product_width_mm:g} mm"},
                    {"Item": "Shipment Qty", "Value": plan.shipment_qty},
                    {"Item": "Yield", "Value": f"{plan.yield_percent:g}%"},
                    {"Item": "Required Production Qty", "Value": plan.required_production_qty},
                    {"Item": "Required Master Rolls", "Value": plan.required_master_rolls},
                    {"Item": "Number of MR Entered", "Value": len(parsed_master_rolls)},
                    {"Item": "Total Actual Small Rolls", "Value": total_actual},
                    {"Item": "Selected Slitters", "Value": ", ".join(selected_slitters)},
                    {"Item": "Starting Slitting Sequence", "Value": f"{starting_sequence:05d}"},
                    {"Item": "Ending Slitting Sequence", "Value": f"{ending_sequence:05d}"},
                    {"Item": "Next Slitting Sequence", "Value": f"{next_sequence:05d}"},
                ]
            )
            st.dataframe(summary, hide_index=True, use_container_width=True)

            preview_columns = {
                "SR Barcode": "小分切条码",
                "Product Width mm": "产品宽度（毫米）",
                "Master Roll SN": "涂覆条码",
                "Assigned Slitter": "分配机台",
                "Slitting Position": "小分切工位",
                "Slitting Sequence": "小分切流水",
                "LOT ID": "批次号",
            }
            with st.expander("条码明细"):
                st.dataframe(
                    pd.DataFrame(generated_rows)[list(preview_columns)].rename(columns=preview_columns),
                    hide_index=True,
                    use_container_width=True,
                )

            st.header("8. Export Excel")
            st.dataframe(
                build_mes_dataframe(generated_rows),
                hide_index=True,
                use_container_width=True,
            )
            excel_bytes = result["excel"]
            st.download_button(
                "Download MES Excel File",
                data=excel_bytes,
                file_name="MES_Slitting_Barcode.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
            )
    else:
        st.session_state.pop("generated_result", None)
        st.info("Complete valid allocation and Master Roll input before generation.")
else:
    st.session_state.pop("generated_result", None)
    st.info("Enter production data and calculate the production plan to begin.")
