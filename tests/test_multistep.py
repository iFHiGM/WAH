import os
print('Step 1: Script Execution Started')
verification_path = 'tests/verification.txt'
with open(verification_path, 'w') as f:
    f.write('Step 2: File Write Successful')
print('Step 3: Script Execution Finished')

# Cleanup
if os.path.exists(verification_path):
    os.remove(verification_path)
    print('Step 4: Cleanup Successful')