# TODO: Look into whether we can consolidate this with 12w_passage_static

from opentrons import protocol_api
from opentrons import types

metadata = {"apiLevel": "2.12"}

# Constants to change for your specific protocol
SOURCE_PLATE_TYPE = "corning_12_wellplate_6.9ml_flat"
SOURCE_PLATE_DECK_SLOT = 1
TRANSFERS = [
    {
        "source_well":"A1",
        "dest_well":"A1",
        "volume_ul":1000
    },
    {
        "source_well":"B1",
        "dest_well":"B1",
        "volume_ul":1000
    }
    ]
MIX_PARAMS = {
    "volume": 1000,
    "num_mixes_at_each_point": 3,
    "mm_from_center": 7.5, #Number of mm from center of well to mix at for each corner
    "mm_from_bottom": 2.5, #Number of mm from bottom of the well to aspirate and dispense at for mixing
    "mix_rate": 5.5 #flow rate, 1.0 is the opentrons default
    }
DESTINATION_PLATE_TYPE = "corning_12_wellplate_6.9ml_flat"
DESTINATION_PLATE_SLOT = 2
PIPETTE_TYPE = "p1000_single_gen2"
PIPETTE_SIDE = "left"
TIPRACK_TYPE = "opentrons_96_filtertiprack_1000ul"
TIPRACK_SLOT = 4
TIPRACK_TIPS = ["A1","B1"] #Array of tips in tip box to consume in order

def run(
    protocol: protocol_api.ProtocolContext
):
    # Defining on-deck plates/consumables
    source_plate = protocol.load_labware(SOURCE_PLATE_TYPE, SOURCE_PLATE_DECK_SLOT)
    destination_plate = protocol.load_labware(DESTINATION_PLATE_TYPE, DESTINATION_PLATE_SLOT)
    tiprack = protocol.load_labware(TIPRACK_TYPE, TIPRACK_SLOT)

    # Define pipette you are using
    pipette = protocol.load_instrument(PIPETTE_TYPE, PIPETTE_SIDE, tip_racks=[tiprack])

    tips_to_consume = iter(TIPRACK_TIPS)

    def compass_mix_pattern(
        plate,
        well,
        num_mixes_at_each_point,
        mm_from_center,
        volume,
        mm_from_bottom,
        mix_rate,
    ):
        # mix center
        pipette.mix(
            num_mixes_at_each_point, volume, plate[well].bottom(mm_from_bottom), rate=mix_rate
        )

        # mix north
        plate.set_offset(
            x=0,
            y=mm_from_center,
            z=0,
        )
        pipette.mix(
            num_mixes_at_each_point, volume, plate[well].bottom(mm_from_bottom), rate=mix_rate
        )

        # mix south
        plate.set_offset(
            x=0,
            y=0 - mm_from_center,
            z=0,
        )
        pipette.mix(
            num_mixes_at_each_point, volume, plate[well].bottom(mm_from_bottom), rate=mix_rate
        )

        # mix east
        plate.set_offset(
            x=mm_from_center,
            y=0,
            z=0,
        )
        pipette.mix(
            num_mixes_at_each_point, volume, plate[well].bottom(mm_from_bottom), rate=mix_rate
        )

        # mix west
        plate.set_offset(
            x=0 - mm_from_center,
            y=0,
            z=0,
        )
        pipette.mix(
            num_mixes_at_each_point, volume, plate[well].bottom(mm_from_bottom), rate=mix_rate
        )

        # Reset the offset back to the original after mixing
        plate.set_offset(
            x=0,
            y=0,
            z=0,
        )

    # add volume to all wells
    for transfer in TRANSFERS:
        next_tip = tiprack.next_tip(starting_tip=tiprack[next(tips_to_consume)])
        pipette.pick_up_tip(next_tip)
        dest_well = transfer["dest_well"]
        source_well = transfer["source_well"]
        pipette.move_to(source_plate[source_well].top(2))
        compass_mix_pattern(
            source_plate,
            source_well,
            MIX_PARAMS["num_mixes_at_each_point"],
            MIX_PARAMS["mm_from_center"],
            MIX_PARAMS["volume"],
            MIX_PARAMS["mm_from_bottom"],  
            MIX_PARAMS["mix_rate"]
        )
        pipette.aspirate(transfer["volume_ul"], source_plate[source_well].bottom())
        pipette.move_to(source_plate[dest_well].top(2))
        pipette.move_to(destination_plate[dest_well].top(40))
        pipette.dispense(transfer["volume_ul"], destination_plate[dest_well].bottom())
        pipette.move_to(destination_plate[dest_well].top(40))
        pipette.drop_tip()

    protocol.home()
