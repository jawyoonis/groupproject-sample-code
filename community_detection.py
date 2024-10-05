import json
import networkx as nx
import community.community_louvain as community_louvain
import plotly.graph_objects as go
import streamlit as st
from matplotlib import cm
import pandas as pd

# Streamlit configuration
st.set_page_config(page_title="Enhanced Community Detection Visualization", layout="wide")

# Title of the app
st.title("Interactive and Enhanced Community Detection in Social Networks")

# File uploader
uploaded_file = st.file_uploader("Upload a JSON file with user and friend data", type=["json"])

# Sidebar for selecting the number of communities
top_n = st.sidebar.slider("Select Number of Top Communities to Display", min_value=1, max_value=10, value=5)

if uploaded_file:
    # Read and parse the uploaded JSON file
    data = json.load(uploaded_file)

    # Build the graph from the JSON data
    def build_graph(data):
        G = nx.Graph()
        for user_id, user_data in data.items():
            G.add_node(user_data['user_info']['id'], name=user_data['user_info']['name'])
            for friend in user_data['friends']:
                friend_id = friend['id']
                G.add_node(friend_id, name=friend['name'])
                G.add_edge(user_data['user_info']['id'], friend_id)
        return G

    # Apply Louvain algorithm for community detection
    def detect_communities(G):
        partition = community_louvain.best_partition(G)
        nx.set_node_attributes(G, partition, 'community')
        return partition

    # Filter the top N communities by number of members
    def filter_top_communities_by_size(G, partition, top_n=5):
        community_sizes = {}
        for node, community in partition.items():
            if community not in community_sizes:
                community_sizes[community] = 0
            community_sizes[community] += 1

        top_communities = sorted(community_sizes, key=community_sizes.get, reverse=True)[:top_n]
        nodes_to_keep = [node for node in G.nodes if partition[node] in top_communities]
        filtered_graph = G.subgraph(nodes_to_keep)
        
        return filtered_graph

    # Generate a list of distinct colors for communities
    def get_community_colors(partition):
        unique_communities = list(set(partition.values()))
        color_map = cm.get_cmap('tab20', len(unique_communities))  # Use a tab20 colormap
        community_colors = {community: color_map(i) for i, community in enumerate(unique_communities)}
        # Convert RGBA tuples to 'rgba(r, g, b, a)' strings
        community_colors = {community: 'rgba({},{},{},{})'.format(int(r*255), int(g*255), int(b*255), a)
                            for community, (r, g, b, a) in community_colors.items()}
        return community_colors

    # Create an interactive Plotly graph
    def create_interactive_plot(G, partition):
        # Use Kamada-Kawai layout for better node spacing
        pos = nx.kamada_kawai_layout(G)
        edge_x = []
        edge_y = []

        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_x = []
        node_y = []
        node_text = []
        node_color = []
        node_size = []

        # Calculate degree centrality for node sizing
        degree_centrality = nx.degree_centrality(G)

        # Generate community colors
        community_colors = get_community_colors(partition)

        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(G.nodes[node]['name'])
            node_color.append(community_colors[partition[node]])  # Use formatted colors for communities
            node_size.append(10 + 70 * degree_centrality[node])  # Size nodes based on centrality, larger size

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            text=node_text,
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='Viridis',
                size=node_size,
                color=node_color,
                opacity=0.8,
                colorbar=dict(
                    thickness=15,
                    title='Community',
                    xanchor='left',
                    titleside='right'
                )
            )
        )

        fig = go.Figure(data=[edge_trace, node_trace],
                        layout=go.Layout(
                            title='Enhanced Community Clusters in Social Network',
                            titlefont_size=20,
                            showlegend=False,
                            hovermode='closest',
                            margin=dict(b=0, l=0, r=0, t=40),
                            height=800,
                            width=1200,
                            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                        )
        fig.update_layout(autosize=True)
        return fig

    # Identify users that connect multiple communities
    def find_bridge_users(G, partition):
        bridge_users = []
        for node in G.nodes():
            # Find communities of neighbors
            neighbor_communities = set(partition[neighbor] for neighbor in G.neighbors(node))
            # If the user belongs to more than one community, add to bridge list
            if len(neighbor_communities) > 1:
                bridge_users.append({
                    "User ID": node,
                    "User Name": G.nodes[node]['name'],
                    "Communities Connected": len(neighbor_communities)
                })
        return bridge_users

    # Build and filter graph
    G = build_graph(data)
    partition = detect_communities(G)
    filtered_G = filter_top_communities_by_size(G, partition, top_n=top_n)

    # Create the interactive plot
    if len(filtered_G) > 0:
        filtered_partition = {node: partition[node] for node in filtered_G.nodes()}
        fig = create_interactive_plot(filtered_G, filtered_partition)
        st.plotly_chart(fig, use_container_width=True)
        
        # Find and display bridge users
        bridge_users = find_bridge_users(filtered_G, filtered_partition)
        if bridge_users:
            st.subheader("Users Connecting Multiple Communities")
            st.dataframe(pd.DataFrame(bridge_users))
        else:
            st.info("No users connecting multiple communities found.")
    else:
        st.warning("No communities available to display. Try increasing the number of communities.")

else:
    st.info("Please upload a JSON file to get started.")
