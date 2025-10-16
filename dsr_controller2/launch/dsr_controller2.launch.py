# 
#  dsr_controller2
#  Author: ros2_control Development Team
#  
#  Copyright (c) 2025 Doosan Robotics
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from launch import LaunchDescription
from launch.actions import RegisterEventHandler,DeclareLaunchArgument
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


ARGUMENTS = [
    DeclareLaunchArgument(
        'model',
        default_value='a0509',
        description='Robot Model'
    ),
    DeclareLaunchArgument(
        'color',
        default_value='white',
        description='Robot Color'
    ),
    DeclareLaunchArgument('name',  default_value = '',     description = 'NAME_SPACE'     ),
        DeclareLaunchArgument('host',         default_value = '192.168.1.200',      description = 'ROBOT_IP'                ),
        DeclareLaunchArgument('port',         default_value = '12345',          description = 'ROBOT_PORT'              ),
        DeclareLaunchArgument('mode',         default_value = 'real',        description = 'OPERATION MODE'          ),
        DeclareLaunchArgument('model',        default_value = 'a0509',          description = 'ROBOT_MODEL'             ),
        DeclareLaunchArgument('color',        default_value = 'white',          description = 'ROBOT_COLOR'             ),
        DeclareLaunchArgument('rt_host',      default_value = '192.168.1.200', description = 'ROBOT_RT_IP'             ),
        DeclareLaunchArgument('use_sim_time', default_value='false',            description='Use simulation time'       ),
        DeclareLaunchArgument('remap_tf',     default_value = 'false',          description = 'REMAP TF'                ),
    ]	

def generate_launch_description():
    # Get URDF via xacro
    robot_description_content = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [
                    FindPackageShare("dsr_description2"),
                    "xacro",
                    "a0509.urdf.xacro",
                ]
            ),
        ]
    )

    set_config_node = Node(
        package="dsr_bringup2",
        executable="set_config",
        namespace=LaunchConfiguration('name'),
        parameters=[
            {"name":    LaunchConfiguration('name')  }, 
            {"rate":    100         },
            {"standby": 5000        },
            {"command": True        },
            {"host":    LaunchConfiguration('host')  },
            {"port":    LaunchConfiguration('port')  },
            {"mode":    LaunchConfiguration('mode')  },
            {"model":   LaunchConfiguration('model') },
            {"gripper": "none"      },
            {"mobile":  "none"      },
            {"rt_host":  LaunchConfiguration('rt_host')      },
        ],
        output="screen",
    )


    robot_description = {"robot_description": robot_description_content}

    robot_controllers = PathJoinSubstitution(
        [
            FindPackageShare("dsr_controller2"),
            "config",
            "dsr_controller2.yaml",
        ]
    )
    # rviz_config_file = PathJoinSubstitution(
    #     [FindPackageShare("dsr_description2"), "rviz", "default.rviz"]
    # )

    control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        namespace=LaunchConfiguration('name'),
        parameters=[robot_description, robot_controllers],
        remappings=[
            (
                "/forward_position_controller/commands",
                "/position_commands",
            ),
        ],
        output="both",
    )
    robot_state_pub_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        namespace=LaunchConfiguration('name'),
        
        output="both",
        remappings=[
            (
                "/joint_states",
                "/dsr/joint_states",
            ),
        ],
        parameters=[robot_description],
    )
    # rviz_node = Node(
    #     package="rviz2",
    #     executable="rviz2",
    #     name="rviz2",
    #     namespace=LaunchConfiguration('name'),
    #     output="log",
    #     arguments=["-d", rviz_config_file],
    # )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        namespace=LaunchConfiguration('name'),
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    robot_controller_spawner = Node(
        package="controller_manager",
        namespace=LaunchConfiguration('name'),
        executable="spawner",
        arguments=["dsr_controller2", "-c", "/controller_manager"],
        parameters=[
            {"host": "192.168.1.200"},
        ],
    )
    
    joint_trajectory_controller_spawner = Node(
        package="controller_manager",
        namespace=LaunchConfiguration('name'),
        executable="spawner",
        arguments=["dsr_joint_trajectory", "-c", "/controller_manager"],
    )

    # joint_state_publisher_spawner = Node(
    #     package="controller_manager",
    #     executable="spawner",
    #     arguments=["dsr_joint_publisher", "--controller-manager", "/controller_manager"],
    # )

    # Delay rviz start after `joint_state_broadcaster`
    # delay_rviz_after_joint_state_broadcaster_spawner = RegisterEventHandler(
    #     event_handler=OnProcessExit(
    #         target_action=joint_state_broadcaster_spawner,
    #         on_exit=[rviz_node],
    #     )
    # )

    # Delay start of robot_controller after `joint_state_broadcaster`
    delay_robot_controller_spawner_after_joint_state_broadcaster_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[robot_controller_spawner],
        )
    )

    # Delay start of robot_controller after `joint_state_broadcaster`
    delay_robot_controller_spawner_after_joint_trajectory_controller_spawner = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=joint_state_broadcaster_spawner,
            on_exit=[joint_trajectory_controller_spawner],
        )
    )

    nodes = [
        set_config_node,
        control_node,
        robot_state_pub_node,
        joint_state_broadcaster_spawner,
        # joint_state_publisher_spawner,
        # delay_rviz_after_joint_state_broadcaster_spawner,
        delay_robot_controller_spawner_after_joint_state_broadcaster_spawner,
        # delay_robot_controller_spawner_after_joint_trajectory_controller_spawner,
    ]

    return LaunchDescription(ARGUMENTS + nodes)
