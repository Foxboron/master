while read -r buildinfo; read -r metadata; do
	echo "---"
	python ./create_tree.py --submit --buildinfo "$buildinfo" --metadata "$metadata"
done < <(find ./submissions -mindepth 2)
