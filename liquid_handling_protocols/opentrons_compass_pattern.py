from opentrons import protocol_api

"""
Opentrons Compass Pattern Script:

Purpose:
This script is designed to demonstrate a compass mixing pattern that has proved successful in resuspending CAR-T cells in suspension in a 12-well plate.

Description:
1. Constants at the beginning of the script define labware types, deck positions, pipette configurations, and transfer/mixing parameters.
2. The script is configured for a specific source plate and a destination plate, both of 12 wells.
3. A set of transfers is defined where each transfer contains a source well, destination well, and the volume to be transferred.
4. A compass mixing pattern function is defined to ensure thorough mixing in a specified well. The pipette moves to the center, north, south, east, and west points within the well and performs mixing actions.
5. For each transfer defined:
    a. A specific tip from the tiprack is picked based on the predefined tip consumption order.
    b. The pipette goes to the source well, mixes the liquid using the compass mixing pattern.
    c. It then aspirates the defined volume from the source well.
    d. The pipette moves to the destination well and dispenses the liquid.
    e. The used tip is then dropped.

6. After all transfers are completed, the robot's motors are moved to their home positions.

Notes:
- Ensure the defined labware types and positions match the physical setup on the Opentrons deck.
- Ensure that the provided volume, depth, and mixing rate in the compass mixing pattern are suitable for the plate and liquid properties to avoid spillage or insufficient mixing.
"""

metadata = {
    'protocolName': 'Compass Pattern Template Protocol',
    'author': 'Monomer Open-Source', # Modify with your name and email
    'description': 'Automated liquid transfer and mixing in a 12-well plate using OT-2, demonstrating a compass mix pattern',
    'apiLevel': '2.12' # Ensure this matches the version of Opentrons you are using
}

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

    # Define the tip array to iterate through
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
        """
        Performs a mixing pattern in a specified well of a plate using a compass pattern: center, north, south, east, and west.
        
        This method moves the pipette to specified points in the well (following the compass directions)
        and then mixes the contents. It is designed to ensure thorough mixing in different parts of the well.
        The order is Mix Center -> North -> South -> East -> West

        Parameters:
        - plate (object): The plate object where the specified well is located.
        - well (str): The well in the plate where the mixing is to be performed.
        - num_mixes_at_each_point (int): The number of mix repetitions to be done at each compass point.
        - mm_from_center (float): The distance in millimeters from the center of the well to move in the N/S/E/W directions.
        - volume (float): The volume in microliters to be aspirated and dispensed during each mix.
        - mm_from_bottom (float): The distance in millimeters from the bottom of the well where the mixing should occur.
        - mix_rate (float): The rate of mixing, usually a value between 0.1 (slow) and 10 (fast).

        After mixing at all the compass points, the function resets the offset of the pipette to its original position.

        Note:
        Ensure that the provided volume, depth, and mixing rate are suitable for the plate and liquid properties
        to avoid spillage or insufficient mixing.
        """
        
        # [rest of the method...]
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
