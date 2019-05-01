while read -r buildinfo; read -r metadata; do
	echo "---"
	curl -F "metadata=@$metadata" -F "buildinfo=@$buildinfo" 127.0.0.1:5000/api/rebuilder/submit
done < <(find ./submissions -mindepth 2)
